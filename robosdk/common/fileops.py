# Copyright 2021 The KubeEdge Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import concurrent.futures
import os
import re
import shutil
import tempfile
from glob import glob
from typing import Dict
from urllib.parse import urlparse

from robosdk.common.config import BaseConfig
from tqdm import tqdm

__all__ = ("FileOps",)


class FileOps:
    """
    This is a class with some class methods to handle some files or folder.
    """

    _S3_PREFIX = "s3://"
    _OBS_PREFIX = "obs://"
    _LOCAL_PREFIX = "file://"
    _URI_RE = "https?://(.+)/(.+)"
    _HTTP_PREFIX = "http(s)://"
    _HEADERS_SUFFIX = "-headers"
    SUPPORT_PROTOCOLS = (_OBS_PREFIX, _S3_PREFIX, _LOCAL_PREFIX, _HTTP_PREFIX)
    _ENDPOINT_NAME = BaseConfig.FILE_TRANS_ENDPOINT_NAME
    _AUTH_AK_NAME = BaseConfig.FILE_TRANS_AUTH_AK_NAME
    _AUTH_SK_NAME = BaseConfig.FILE_TRANS_AUTH_SK_NAME

    @classmethod
    def _normalize_uri(cls, uri: str) -> str:
        for src, dst in [
            ("/", cls._LOCAL_PREFIX),
            (cls._OBS_PREFIX, cls._S3_PREFIX)
        ]:
            if uri.startswith(src):
                return uri.replace(src, dst, 1)
        return uri

    @classmethod
    def download(cls, src: str, dst: str = None, untar: bool = False,
                 method: str = "", headers: Dict = None, cookies: Dict = None):
        """
        Download files to local directory from remote.
        """

        src = cls._normalize_uri(src)
        basename = os.path.basename(src)
        if dst is None:
            dst = tempfile.mkdtemp()
        else:
            dst = re.sub(re.escape(basename) + "$", "", dst)
            os.makedirs(dst, exist_ok=True)

        if src.startswith(cls._S3_PREFIX):
            dst = cls.download_s3(src, dst)
        elif src.startswith(cls._LOCAL_PREFIX):
            dst = cls.download_local(src, dst)
        elif re.search(cls._URI_RE, src):
            method = str(method).upper() if method else "GET"
            dst = cls.download_from_uri(src, dst, method=method,
                                        headers=headers, cookies=cookies)
        else:
            raise Exception("Cannot recognize storage type for %s.\n"
                            "%r are the current available storage type." %
                            (src, cls.SUPPORT_PROTOCOLS))
        if os.path.isdir(dst):
            _dst = os.path.join(dst, basename)
            if os.path.exists(_dst):
                dst = _dst
        if untar:
            if os.path.isfile(dst):
                return cls._untar(dst)
            if os.path.isdir(dst):
                _ = map(cls._untar, glob(os.path.join(dst, "*")))
        return dst

    @classmethod
    def upload(cls, src: str, dst: str,
               tar: bool = False, clean: bool = False,
               method: str = "", headers: Dict = None, cookies: Dict = None):
        """
        Upload the local files to remote.
        """
        basename = os.path.basename(src)
        dst = cls._normalize_uri(dst)
        dst = re.sub(re.escape(basename) + "$", "", dst)
        if tar:
            src = cls._tar(src, f"{src.rstrip(os.path.sep)}.tar.gz")
        if dst.startswith(cls._S3_PREFIX):
            dst = cls.upload_s3(src, dst)
        elif dst.startswith(cls._LOCAL_PREFIX):
            if not os.path.isdir(dst):
                os.makedirs(dst)
            dst = cls.download_local(src, dst)
        elif re.search(cls._URI_RE, src):
            method = str(method).upper() if method else "POST"
            dst = cls.upload_to_uri(src, dst, method=method,
                                    headers=headers, cookies=cookies)
        else:
            raise Exception("Cannot recognize storage type for %s.\n"
                            "%r are the current available storage type." %
                            (src, cls.SUPPORT_PROTOCOLS))
        if clean and os.path.exists(src):
            cls.delete(src)
        return dst

    @classmethod
    def download_s3(cls, uri: str, out_dir: str) -> str:
        client = cls._create_minio_client()
        return cls._download_s3(client, uri, out_dir)

    @classmethod
    def download_local(cls, uri: str, out_dir: str) -> str:
        local_path = uri.replace(cls._LOCAL_PREFIX, "/", 1)

        dest_path = os.path.join(
            os.path.join(out_dir, os.path.basename(local_path))
        ) if os.path.isdir(out_dir) else out_dir
        if os.path.isdir(local_path):
            shutil.copytree(local_path, dest_path, dirs_exist_ok=True)
        elif os.path.isfile(local_path):
            if not os.path.samefile(local_path, dest_path):
                shutil.copy(local_path, dest_path)

        return out_dir

    @classmethod
    def download_from_uri(cls, uri: str, local_path: str,
                          method: str = "GET",
                          headers: Dict = None,
                          cookies: Dict = None):
        client = cls._create_http_client()
        if headers:
            client.set_header(headers)
        if cookies:
            client.set_header(cookies)
        f_name = os.path.basename(uri) or "download_file"
        if os.path.isdir(local_path):
            local_path = os.path.join(local_path, f_name)
        resp = client.download(url=uri, dst_file=local_path,
                               method=method)
        if resp and hasattr(resp, "content"):
            return resp.content
        return

    @classmethod
    def upload_s3(cls, src, dst):

        s3 = cls._create_minio_client()
        parsed = urlparse(dst, scheme='s3')
        bucket_name = parsed.netloc

        def _s3_upload(_file, fname=""):
            _file_handle = open(_file, 'rb')
            _file_handle.seek(0, os.SEEK_END)
            size = _file_handle.tell()
            _file_handle.seek(0)
            if not fname:
                fname = os.path.basename(fname)
            bucket = s3.bucket_exists(bucket_name)
            if not bucket:
                s3.make_bucket(bucket_name)
            s3.put_object(bucket_name, fname, _file_handle, size)
            _file_handle.close()
            return size

        if os.path.isdir(src):
            for root, _, files in tqdm(os.walk(src)):
                for file in files:
                    filepath = os.path.join(root, file)
                    name = os.path.relpath(filepath, src)
                    _s3_upload(filepath, name)
        elif os.path.isfile(src):
            _s3_upload(src, parsed.path.lstrip("/"))

        return dst

    @classmethod
    def upload_to_uri(cls, local_path: str, uri: str,
                      method: str = "POST",
                      headers: Dict = None,
                      cookies: Dict = None):
        client = cls._create_http_client()
        if headers:
            client.set_header(headers)
        if cookies:
            client.set_header(cookies)

        def _http_upload(_file, fname=""):
            _file_handle = open(_file, 'rb')
            if not fname:
                fname = os.path.basename(fname)
            client.add(
                url=uri, method=method,
                files={"file": _file_handle},
                data={"name": fname}
            )
            _file_handle.close()

        if os.path.isdir(local_path):
            for root, _, files in tqdm(os.walk(local_path)):
                for file in files:
                    filepath = os.path.join(root, file)
                    name = os.path.basename(filepath)
                    _http_upload(filepath, name)
        elif os.path.isfile(local_path):
            _http_upload(local_path, os.path.basename(local_path))
        client.run()
        return uri

    @classmethod
    def _create_minio_client(cls):
        import minio

        ctx = BaseConfig.DYNAMICS_CONFING
        _url = ctx.get(cls._ENDPOINT_NAME, "http://s3.amazonaws.com")
        _ak = ctx.get(cls._AUTH_AK_NAME, None) if cls._AUTH_AK_NAME else None
        _sk = ctx.get(cls._AUTH_SK_NAME, None) if cls._AUTH_SK_NAME else None
        if not (_url.startswith("http://") or _url.startswith("https://")):
            _url = f"https://{_url}"
        url = urlparse(_url)
        use_ssl = url.scheme == 'https' if url.scheme else True
        client = minio.Minio(
            url.netloc, access_key=_ak,
            secret_key=_sk, secure=use_ssl
        )
        return client

    @classmethod
    def _create_http_client(cls):
        from aiohttp import BasicAuth
        from robosdk.utils.request import AsyncRequest

        ctx = BaseConfig.DYNAMICS_CONFING
        _ak = ctx.get(cls._AUTH_AK_NAME, None) if cls._AUTH_AK_NAME else None
        _sk = ctx.get(cls._AUTH_SK_NAME, None) if cls._AUTH_SK_NAME else None

        auth = None
        token = ''
        if _ak and _sk:
            auth = BasicAuth(_ak, _sk)
        elif _ak:
            token = str(_ak)
        client = AsyncRequest(token=token, auth=auth)

        return client

    @classmethod
    def _download_s3_with_multi_files(cls, download_files,
                                      base_uri, base_out_dir):

        client = cls._create_minio_client()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            todos = []
            for dfile in tqdm(download_files):
                dir_ = os.path.dirname(dfile)
                uri = os.path.join(base_uri.rstrip("/"), dfile)
                out_dir = os.path.join(base_out_dir, dir_)
                todos.append(executor.submit(cls._download_s3,
                                             client, uri, out_dir))

            for done in concurrent.futures.as_completed(todos):
                count = done.result()
                if count == 0:
                    continue
        return base_out_dir

    @classmethod
    def _download_s3(cls, client, uri, out_dir):
        """
        The function downloads specified file or folder to local directory.
        this function supports:
        1. when downloading the specified file, keep the name of the file.
        2. when downloading the specified folder, keep the name of the folder.
        Parameters:
        client: s3 client
        s3_url(string): url in s3, e.g. file url: s3://dev/data/data.txt,
                        directory url: s3://dev/data
        out_dir(string):  local directory address, e.g. /tmp/data/
        Returns:
        int: files of number in s3_url
        """
        bucket_args = uri.replace(cls._S3_PREFIX, "", 1).split("/", 1)
        bucket_name = bucket_args[0]
        bucket_path = len(bucket_args) > 1 and bucket_args[1] or ""

        objects = client.list_objects(bucket_name,
                                      prefix=bucket_path,
                                      recursive=True,
                                      use_api_v1=True)
        root_path = os.path.split(os.path.normpath(bucket_path))[0]
        for obj in tqdm(objects):
            # Replace any prefix from the object key with out_dir
            subdir_object_key = obj.object_name[len(root_path):].strip("/")
            # fget_object handles directory creation if does not exist
            if not obj.is_dir:
                local_file = os.path.join(
                    out_dir,
                    subdir_object_key or os.path.basename(obj.object_name)
                )
                client.fget_object(bucket_name, obj.object_name, local_file)
        return out_dir

    @classmethod
    def _untar(cls, src, dst=None):
        import tarfile
        import zipfile
        if not (os.path.isfile(src) and str(src).endswith((".gz", ".zip"))):
            return src
        if dst is None:
            dst = os.path.dirname(src)
        _bname, _bext = os.path.splitext(os.path.basename(src))
        if _bext == ".zip":
            with zipfile.ZipFile(src, 'r') as zip_ref:
                zip_ref.extractall(dst)
        else:
            with tarfile.open(src, 'r:gz') as tar_ref:
                tar_ref.extractall(path=dst)
        if os.path.isfile(src):
            cls.delete(src)
        checkname = os.path.join(dst, _bname)
        return checkname if os.path.exists(checkname) else dst

    @classmethod
    def _tar(cls, src, dst) -> str:
        import tarfile
        with tarfile.open(dst, 'w:gz') as tar:
            if os.path.isdir(src):
                for root, _, files in os.walk(src):
                    for file in files:
                        filepath = os.path.join(root, file)
                        tar.add(filepath)
            elif os.path.isfile(src):
                tar.add(os.path.realpath(src))
        return dst

    @classmethod
    def delete(cls, path):

        # noinspection PyBrodException
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            if os.path.isfile(path):
                os.remove(path)
        except Exception: # noqa
            pass


def test_file_ops():
    FileOps.upload("/tmp/text.rst", "s3://smart-open-test/")
    FileOps.download("s3://smart-open-test/", "/tmp")