"""
Secret Databases пайплайны - доступ к секретным базам данных
"""

from .scihub_mirrors import SciHubMirrorsPipeline
from .libgen_p2p import LibGenP2PPipeline
from .academic_torrents import AcademicTorrentsPipeline
from .research_data_vault import ResearchDataVaultPipeline
from .open_access_journals import OpenAccessJournalsPipeline

__all__ = [
    'SciHubMirrorsPipeline',
    'LibGenP2PPipeline',
    'AcademicTorrentsPipeline',
    'ResearchDataVaultPipeline',
    'OpenAccessJournalsPipeline'
]
