#!/usr/bin/python
#
# Copyright 2019 Nate Walck
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
"""autopkg processor to run ipfs import"""

import subprocess
from FoundationPlist import readPlist, writePlist

from autopkglib import Processor, ProcessorError

__all__ = ["IPFSAdd"]


class IPFSAdd(Processor):
    """Runs ipfs import on an item"""

    input_variables = {
        "pkginfo_repo_path": {
          "required": True,
          "description": "Path to pkginfo"
        },
        "pkg_repo_path": {
            "required": True,
            "description": "Path to imported pkg",
        },
    }
    output_variables = {
        "ipfs_cid": {
            "description": "CID of the imported item."
        },
    }

    description = __doc__

    def main(self):
        """Import item into IPFS"""
        if len(self.env['pkginfo_repo_path']) < 1:
            self.output('empty pkginfo path')
            return
        pkginfo = readPlist(self.env['pkginfo_repo_path'])
        # Generate arguments for makecatalogs.
        args = ["/usr/local/bin/ipfs", "add", "--only-hash"]
        if self.env["pkg_repo_path"].startswith("/"):
            # looks a file path instead of a URL
            args.append(self.env["pkg_repo_path"])

        # Call ipfs add.
        try:
            proc = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            (output, err_out) = proc.communicate()
        except OSError as err:
            raise ProcessorError(
                "ipfs add failed with error code %d: %s"
                % (err.errno, err.strerror)
            )

        self.env["ipfs_cid"] = str(output).split(' ')[1]
        self.env["ipfs_add_resultcode"] = proc.returncode
        self.env["ipfs_add_stderr"] = err_out.decode("utf-8")
        if proc.returncode != 0:
            error_text = "IPFS add failed: \n" + self.env["ipfs_add_stderr"]
            raise ProcessorError(error_text)
        else:
            pkginfo['ipfs_cid'] = self.env["ipfs_cid"]
            self.output(
                'Writing pkginfo to %s' %
                self.env['pkginfo_repo_path']
            )
            writePlist(pkginfo, self.env['pkginfo_repo_path'])
            self.output("{} added to IPFS with cid {}".format(
                self.env["pkg_repo_path"],
                self.env["ipfs_cid"]
                )
            )


if __name__ == "__main__":
    PROCESSOR = IPFSAdd()
    PROCESSOR.execute_shell()
