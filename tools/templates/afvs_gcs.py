#!/usr/bin/env python3

# Copyright (C) 2019 Christoph Gorgulla
#
# This file is part of AdaptiveFlow.
#
# AdaptiveFlow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# AdaptiveFlow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with AdaptiveFlow.  If not, see <https://www.gnu.org/licenses/>.

# ---------------------------------------------------------------------------
#
# Description: Google Cloud Storage access for AdaptiveFlow.
#
#   Provides a single narrow interface (ObjectStore) with two
#   implementations:
#
#     * GCSObjectStore   - google-cloud-storage backed, used in production.
#     * LocalObjectStore - filesystem backed, used by the offline test suite
#                          and by local verification runs. Objects live under
#                          <root>/<bucket>/<object_name>, so no network or
#                          credentials are involved.
#
#   Both are addressed with a separate (bucket, object_name) pair and never
#   with a "gs://" URI. Object names are validated so that a URI accidentally
#   passed where a key is expected is rejected loudly instead of being handed
#   to a filesystem or boto3 reader.
#
# Revision history:
# 2026-11-18  Original version
#
# ---------------------------------------------------------------------------

import base64
import hashlib
import logging
import os
import re
import shutil
from pathlib import Path, PureWindowsPath

logger = logging.getLogger(__name__)

GCS_URI_RE = re.compile(r'^gs://(?P<bucket>[^/]+)/(?P<object_name>.+)$')

# Environment variable that points the GCS layer at a local directory
# instead of the Google Cloud Storage API. Used by the offline test suite,
# by `--local-object-store` on the command line tools, and by local
# verification workers. When set, no Google API client is constructed.
LOCAL_OBJECT_STORE_ENV = 'AFVS_GCS_LOCAL_ROOT'


class ObjectStoreError(Exception):
    """Raised for object store problems that the caller is expected to handle."""


class ObjectNotFound(ObjectStoreError):
    """Raised when a requested object does not exist."""


def parse_gcs_uri(uri):
    """Splits a gs:// URI into its bucket and object name.

    Args:
        uri (str): A URI of the form gs://bucket/object/name.

    Returns:
        (bucket, object_name) tuple of str.

    Raises:
        ObjectStoreError: If the value is not a gs:// URI.
    """
    match = GCS_URI_RE.match(str(uri).strip())
    if not match:
        raise ObjectStoreError(f"Not a gs:// URI: {uri!r}")
    return match.group('bucket'), match.group('object_name')


def format_gcs_uri(bucket, object_name):
    """Builds a gs:// URI for display and logging purposes only."""
    return f"gs://{bucket}/{object_name.lstrip('/')}"


def validate_object_name(object_name):
    """Checks that a value is usable as a GCS object name.

    A gs:// URI is explicitly rejected: callers must keep the bucket and the
    object name separate so that neither a filesystem reader nor boto3 is
    ever handed a URI it cannot interpret.

    Args:
        object_name (str): Candidate object name.

    Returns:
        The object name with any leading slashes removed.

    Raises:
        ObjectStoreError: If the name is empty, a URI, or path-traversing.
    """
    if object_name is None:
        raise ObjectStoreError("Object name must not be None")

    name = str(object_name)

    if name.startswith("gs://") or name.startswith("s3://"):
        raise ObjectStoreError(
            f"Object name must be a bare object key, not a URI: {name!r}")

    if "\\" in name:
        # A backslash is a path separator on Windows, so it would escape
        # the filesystem-backed store that the offline and local
        # verification runs use. AFVS object names never contain one.
        raise ObjectStoreError(
            f"Object name must use '/' separators only: {name!r}")

    name = name.lstrip("/")

    if name == "":
        raise ObjectStoreError("Object name must not be empty")

    if PureWindowsPath(name).is_absolute() or PureWindowsPath(name).drive:
        # Windows path semantics are checked on every platform: pathlib
        # only recognizes a drive letter in a Windows path, so a POSIX
        # host would otherwise accept a name that escapes the store as
        # soon as the same local store is read on Windows.
        raise ObjectStoreError(
            f"Object name must be relative, not an absolute path: {name!r}")

    parts = name.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ObjectStoreError(
            f"Object name must not contain empty or relative path segments: {name!r}")

    return name


def file_md5_b64(path):
    """Returns the base64-encoded MD5 digest of a local file, as GCS reports it."""
    digest = hashlib.md5()
    with open(path, "rb") as read_file:
        for chunk in iter(lambda: read_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return base64.b64encode(digest.digest()).decode("ascii")


def file_sha256_hex(path):
    """Returns the hex SHA-256 digest of a local file."""
    digest = hashlib.sha256()
    with open(path, "rb") as read_file:
        for chunk in iter(lambda: read_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ObjectStore:
    """Minimal object store interface used by the AdaptiveFlow GCP paths."""

    #: Human readable backend name, used in logs and manifests.
    backend = "abstract"

    def upload_file(self, local_path, bucket, object_name):
        """Uploads a local file and returns an object metadata dict."""
        raise NotImplementedError

    def download_file(self, bucket, object_name, local_path):
        """Downloads an object to a local path and returns its metadata dict."""
        raise NotImplementedError

    def stat(self, bucket, object_name):
        """Returns an object metadata dict, or raises ObjectNotFound."""
        raise NotImplementedError

    def exists(self, bucket, object_name):
        """Returns True when the object exists."""
        try:
            self.stat(bucket, object_name)
        except ObjectNotFound:
            return False
        return True

    def list_objects(self, bucket, prefix):
        """Returns a sorted list of object names under a prefix."""
        raise NotImplementedError

    def delete_object(self, bucket, object_name):
        """Deletes an object. Missing objects are not an error."""
        raise NotImplementedError

    def download_and_verify(self, bucket, object_name, local_path, expected_size=None,
                            expected_md5_b64=None):
        """Downloads an object and verifies its size and MD5 before returning.

        A truncated or substituted archive is rejected here rather than
        surfacing later as an unreadable tar file.

        Args:
            bucket (str): Bucket name.
            object_name (str): Object key.
            local_path (str): Destination path.
            expected_size (int): Optional expected size in bytes.
            expected_md5_b64 (str): Optional expected base64 MD5 digest.

        Returns:
            The object metadata dict, with 'local_md5' added.

        Raises:
            ObjectNotFound: If the object does not exist.
            ObjectStoreError: If verification fails.
        """
        metadata = self.download_file(bucket, object_name, local_path)

        local_size = os.path.getsize(local_path)
        reference_size = expected_size if expected_size is not None else metadata.get('size')
        if reference_size is not None and int(reference_size) != int(local_size):
            raise ObjectStoreError(
                f"Size mismatch for {format_gcs_uri(bucket, object_name)}: "
                f"expected {reference_size} bytes, got {local_size} bytes")

        local_md5 = file_md5_b64(local_path)
        metadata['local_md5'] = local_md5

        reference_md5 = expected_md5_b64 if expected_md5_b64 is not None else metadata.get('md5')
        if reference_md5 is not None and reference_md5 != local_md5:
            raise ObjectStoreError(
                f"MD5 mismatch for {format_gcs_uri(bucket, object_name)}: "
                f"expected {reference_md5}, got {local_md5}")

        return metadata


class LocalObjectStore(ObjectStore):
    """Filesystem-backed object store used for offline verification.

    Objects are stored as <root>/<bucket>/<object_name>. This is the mock
    object storage the offline acceptance tests replay tasks against; it
    performs no network access of any kind.
    """

    backend = "local"

    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, bucket, object_name):
        if not bucket:
            raise ObjectStoreError("Bucket name must not be empty")
        name = validate_object_name(object_name)
        return self.root / str(bucket) / name

    def upload_file(self, local_path, bucket, object_name):
        destination = self._path(bucket, object_name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(local_path, destination)
        return self.stat(bucket, object_name)

    def download_file(self, bucket, object_name, local_path):
        source = self._path(bucket, object_name)
        if not source.is_file():
            raise ObjectNotFound(
                f"No such object: {format_gcs_uri(bucket, object_name)}")
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, local_path)
        return self.stat(bucket, object_name)

    def stat(self, bucket, object_name):
        path = self._path(bucket, object_name)
        if not path.is_file():
            raise ObjectNotFound(
                f"No such object: {format_gcs_uri(bucket, object_name)}")
        return {
            'bucket': bucket,
            'object_name': validate_object_name(object_name),
            'size': path.stat().st_size,
            'md5': file_md5_b64(path),
            'backend': self.backend,
        }

    def list_objects(self, bucket, prefix):
        bucket_root = self.root / str(bucket)
        if not bucket_root.is_dir():
            return []

        normalized_prefix = str(prefix or "").lstrip("/")
        results = []
        for path in bucket_root.rglob("*"):
            if not path.is_file():
                continue
            object_name = path.relative_to(bucket_root).as_posix()
            if object_name.startswith(normalized_prefix):
                results.append(object_name)
        return sorted(results)

    def delete_object(self, bucket, object_name):
        path = self._path(bucket, object_name)
        if path.is_file():
            path.unlink()


class GCSObjectStore(ObjectStore):
    """Google Cloud Storage backed object store.

    The google-cloud-storage client is imported lazily so that the AFVS
    tools, the offline test suite and the AWS/Slurm paths keep working on
    installations that do not have the Google client libraries present.
    """

    backend = "gcs"

    def __init__(self, project=None, client=None):
        if client is not None:
            self._client = client
        else:
            try:
                from google.cloud import storage
            except ImportError as error:  # pragma: no cover - depends on env
                raise ObjectStoreError(
                    "google-cloud-storage is required for GCS storage modes. "
                    "Install it with 'pip install google-cloud-storage'.") from error
            self._client = storage.Client(project=project) if project else storage.Client()

    def _blob(self, bucket, object_name):
        name = validate_object_name(object_name)
        return self._client.bucket(str(bucket)).blob(name)

    def upload_file(self, local_path, bucket, object_name):
        blob = self._blob(bucket, object_name)
        blob.upload_from_filename(str(local_path))
        return self._metadata(bucket, object_name, blob)

    def download_file(self, bucket, object_name, local_path):
        blob = self._blob(bucket, object_name)
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            blob.download_to_filename(str(local_path))
        except Exception as error:  # pragma: no cover - requires live GCS
            if _is_not_found(error):
                raise ObjectNotFound(
                    f"No such object: {format_gcs_uri(bucket, object_name)}") from error
            raise
        return self._metadata(bucket, object_name, blob)

    def stat(self, bucket, object_name):
        name = validate_object_name(object_name)
        blob = self._client.bucket(str(bucket)).get_blob(name)
        if blob is None:
            raise ObjectNotFound(
                f"No such object: {format_gcs_uri(bucket, name)}")
        return self._metadata(bucket, name, blob)

    def list_objects(self, bucket, prefix):
        normalized_prefix = str(prefix or "").lstrip("/")
        blobs = self._client.list_blobs(str(bucket), prefix=normalized_prefix)
        return sorted(blob.name for blob in blobs)

    def delete_object(self, bucket, object_name):
        blob = self._blob(bucket, object_name)
        try:
            blob.delete()
        except Exception as error:  # pragma: no cover - requires live GCS
            if not _is_not_found(error):
                raise

    def _metadata(self, bucket, object_name, blob):
        return {
            'bucket': str(bucket),
            'object_name': validate_object_name(object_name),
            'size': blob.size,
            'md5': blob.md5_hash,
            'generation': blob.generation,
            'backend': self.backend,
        }


def _is_not_found(error):
    """Best-effort detection of a GCS 404 without importing google.api_core."""
    code = getattr(error, 'code', None)
    if code == 404:
        return True
    status = getattr(getattr(error, 'response', None), 'status_code', None)
    if status == 404:
        return True
    return type(error).__name__ == "NotFound"


def object_store_from_env(project=None, local_root=None):
    """Builds the object store that the current environment asks for.

    A local root (explicit argument or AFVS_GCS_LOCAL_ROOT) selects the
    filesystem-backed store. This is what keeps the offline test suite and
    local verification runs from making any Google API calls.

    Args:
        project (str): Optional GCP project for the live client.
        local_root (str): Optional local directory for the mock store.

    Returns:
        An ObjectStore implementation.
    """
    root = local_root or os.environ.get(LOCAL_OBJECT_STORE_ENV, "")
    if root:
        logger.info("Using local object store rooted at %s", root)
        return LocalObjectStore(root)
    return GCSObjectStore(project=project)
