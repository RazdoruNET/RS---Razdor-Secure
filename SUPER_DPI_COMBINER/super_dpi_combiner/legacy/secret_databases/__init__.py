"""
Secret Databases пайплайны - доступ к секретным базам данных
"""

from super_dpi_combiner.pipelines.secret_databases.scihub_mirrors import SciHubMirrorsPipeline
from super_dpi_combiner.pipelines.secret_databases.libgen_p2p import LibGenP2PPipeline

__all__ = [
    'SciHubMirrorsPipeline',
    'LibGenP2PPipeline'
]
