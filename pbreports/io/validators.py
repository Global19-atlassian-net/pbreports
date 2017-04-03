import os
import logging
import functools

from pbcore.util.Process import backticks
from pbcommand.utils import nfs_exists_check
from pbcommand.validators import validate_output_dir, validate_fofn, fofn_to_files, validate_report

log = logging.getLogger(__name__)

# For backward compatibility
bas_fofn_to_bas_files = fofn_to_files
