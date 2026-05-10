"""
Secret Databases пайплайны - доступ к секретным базам данных
"""

from pipelines.secret_databases.scihub_mirrors import SciHubMirrorsPipeline
from pipelines.secret_databases.libgen_p2p import LibGenP2PPipeline
from pipelines.secret_databases.academic_torrents import AcademicTorrentsPipeline
from pipelines.secret_databases.research_data_vault import ResearchDataVaultPipeline
from pipelines.secret_databases.open_access_journals import OpenAccessJournalsPipeline

__all__ = [
    'SciHubMirrorsPipeline',
    'LibGenP2PPipeline',
    'AcademicTorrentsPipeline',
    'ResearchDataVaultPipeline',
    'OpenAccessJournalsPipeline'
]
