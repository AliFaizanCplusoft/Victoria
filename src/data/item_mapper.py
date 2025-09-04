"""
Item Mapping System for Psychometric Assessment

Maps assessment items to behavioral constructs and handles
item metadata including reverse scoring and construct groupings.
"""

import pandas as pd
from typing import Dict, List, Optional
import logging

# Core Construct Mapping based on your data analysis
CONSTRUCT_MAPPING = {
    'RT': 'Risk Taking',
    'DA': 'Drive & Ambition', 
    'IO': 'Innovation Orientation',
    'DM': 'Decision Making',
    'RG': 'Resilience & Grit',
    'SL': 'Servant Leadership',
    'TB': 'Team Building',
    'EI': 'Emotional Intelligence',
    'A': 'Accountability',
    'PS': 'Problem Solving',
    'CT': 'Critical Thinking',
    'F': 'Failure Response',
    'AD': 'Adaptability',
    'C': 'Conflict Management',
    'N': 'Negotiation',
    'RB': 'Relationship Building',
    'IN': 'Influence',
    'IIN': 'Interpersonal Intelligence'
}

# Item to Construct mapping based on your 147 items
ITEM_TO_CONSTRUCT = {
    # Risk Taking Items
    'EnergizedByPotential': 'RT',
    'ComfortUnchartedT': 'RT', 
    'Adventurous': 'RT',
    'ComfDecUncert': 'RT',
    'GoBeyondComfZone': 'RT',
    'RiskTkgImport': 'RT',
    'PtMyselfUncomfrtSituations': 'RT',
    
    # Drive & Ambition Items
    'EagertoPursue': 'DA',
    'PursuePerfection': 'DA',
    'Pass2Inovate': 'DA',
    'ShapeMyPath': 'DA',
    'DeterminedReachGls': 'DA',
    'AlwaysMorLearn': 'DA',
    'TackleChallenges': 'DA',
    'MoveForward': 'DA',
    'Persistent': 'DA',
    'DrivenLongTrmSucc': 'DA',
    
    # Innovation Orientation Items
    'CommunIdeas': 'IO',
    'AskQuestions': 'IO',
    'ImCreative': 'IO',
    'InnoExec': 'IO',
    'BelieveBestSolProb': 'IO',
    'ExamMultiPerspctvs': 'IO',
    'MultiScenariosConsidProb': 'IO',
    'AdaptMsg2Audience': 'IO',
    
    # Decision Making Items
    'ActBeforeThinkg': 'DM',
    'StruggleDecs': 'DM',
    'KnowEnuf': 'DM',
    'ThinkWOActing': 'DM',
    'TkTime2UndstndComplxIssues': 'DM',
    'DecsnsNtGoingExpected': 'DM',
    'MakeDecWMissInfo': 'DM',
    'IntentnlChoices': 'DM',
    'ObjectiveDecisions': 'DM',
    'ConsideredBiases': 'DM',
    'Quick2Act': 'DM',
    'ExistFrame4Decisions': 'DM',
    'DpAnalGuideDec': 'DM',
    
    # Resilience & Grit Items
    'DiscourageByFailure': 'RG',
    'GiveUpChallenging': 'RG',
    'SingularFocus': 'RG',
    'ObstaclesAsBlocks': 'RG',
    'Slow2Adapt': 'RG',
    'PivotWhenNeeded': 'RG',
    'HandleFrustration': 'RG',
    'ReflectOnFailure': 'RG',
    'ComfortWFailure': 'RG',
    'Resistant2ChangeAfterFail': 'RG',
    'FailureStopTrying': 'RG',
    'WorseFailures': 'RG',
    'BetterFailurs': 'RG',
    
    # Servant Leadership Items
    'Listen2Others': 'SL',
    'FocusNeedsTeam': 'SL',
    'Legacy2ElevateOthers': 'SL',
    'ValueInputFromAll': 'SL',
    'WholeTeamSucc': 'SL',
    'TakeResp4Setbacks': 'SL',
    'PersonalGainsRImportant': 'SL',
    'CMyTeamGetRecog': 'SL',
    'TakeCreditofMyTeam': 'SL',
    'HumbleInContributions': 'SL',
    'Others2knowWhatIdid': 'SL',
    
    # Team Building Items
    'ImAGoodListener': 'TB',
    'SpeakUp@Mtgs': 'TB',
    'TrustEss4Innovation': 'TB',
    'ConfidentAbility2Assemble': 'TB',
    'StrongTeamPerform': 'TB',
    'TrustIndWRespons': 'TB',
    'ProvGuidance2Teams': 'TB',
    'BelieveValRelations': 'TB',
    'Adapt2DiffDynamics': 'TB',
    'IDindividTalent': 'TB',
    'OpenComms': 'TB',
    'Vulnerable': 'TB',
    'TeamsDevBetSoluts': 'TB',
    'SafeTeamEnvirons': 'TB',
    'Dependable': 'TB',
    
    # Emotional Intelligence Items
    'DiscernEmotClues': 'EI',
    'DiscEmotTrggrsConflct': 'EI',
    'Slf-Reflct2ImprEmotAwrnss': 'EI',
    'GoodEmpathizg': 'EI',
    'AdaptCommNeedsOthers': 'EI',
    'RemnCompsdNavDisagr': 'EI',
    'Self-Aware': 'EI',
    'ArticulateBiases': 'EI',
    'AskQs': 'EI',
    
    # Accountability Items
    'Procrastinate': 'A',
    'StandbyCommitements': 'A',
    'KeepPromises': 'A',
    'AcknowledgeMistakes': 'A',
    'GoesWrongIsMyFault': 'A',
    'AcceptRespons4Err': 'A',
    'ComfortOwnRespnsOutcms': 'A',
    'Cmmttd2Promises': 'A',
    'AcknowledgeRoleInSucFail': 'A',
    'ProActCommsDlysObstcls': 'A',
    'NoSomthngUnreal': 'A',
    'MeetDeadlines': 'A',
    'LearnFrmMistakes': 'A',
    
    # Problem Solving Items
    'InternReas2Compl': 'PS',
    'Problems2Steps': 'PS',
    'RunThruScenarios': 'PS',
    'ConsiderAssumptns': 'PS',
    'PrepB4Mtg1stTime': 'PS',
    'KnowNonneg': 'PS',
    'Resourceful': 'PS',
    'ConseqPotActions': 'PS',
    
    # Critical Thinking Items
    'ComfortRecFdbkColleag': 'CT',
    'IncorpEmrgInfo': 'CT',
    'AdaptStances': 'CT',
    'Open2Feedback': 'CT',
    'Open2DivPerspctvs': 'CT',
    'ThinkB4Speak': 'CT',
    'Open2Feedback': 'CT',
    
    # Conflict Management Items
    'ComfortwConflict': 'C',
    'ComfortWConstrctvConflict': 'C',
    'DiffBetwnConstr&DestrtvConflct': 'C',
    'AddrssConflctsDirect': 'C',
    'ConflctLeadsBetOutcms': 'C',
    'WantConflictGoAway': 'C',
    'SeprtPersnFrmIssue': 'C',
    'ComfortDelvrngSensFdbk': 'C',
    
    # Adaptability Items
    'ListenB4Spkng': 'AD',
    'ImAdaptivePerson': 'AD',
    'MntnComposureUndPressure': 'AD',
    'InfluencedByOthers': 'AD',
    'ImCollaborative': 'AD',
    
    # Relationship Building Items
    'NurtureConnctns': 'RB',
    'UsePeopl': 'RB',
    'Listen2Others': 'RB',
    'EasilyDistracted': 'RB',
    'MovePstSmllTalk': 'RB',
    'BuildRapportWAnyone': 'RB',
    'MaintainRelationships': 'RB',
    'RelationshpsRTx': 'RB',
    
    # Interpersonal Items
    'ComfortSharIdeasPersSett': 'IIN',
    'Observant': 'IIN',
    'Listener': 'IIN',
    'Reflect': 'IIN',
    'SocialSitsDrainEnergy': 'IIN',
    'EnergizedMtgNewPeop': 'IIN',
    'SpeakUpPitchIdeas': 'IIN',
    'DrvnSocEng': 'IIN',
    'Conversations': 'IIN',
    'PreferActiveParticipate': 'IIN',
    
    # Additional items
    'AnnoyedIfNoIdea': 'EI',
    'FollowTraditions': 'AD',
    'WillingCompromise': 'N',
    'SeeSomeone': 'RB'
}

# Reverse-scored items (based on your CSV analysis)
REVERSE_SCORED_ITEMS = {
    'PursuePerfection',
    'ActBeforeThinkg', 
    'Procrastinate',
    'StruggleDecs',
    'KnowEnuf',
    'DiscourageByFailure',
    'GiveUpChallenging',
    'ObstaclesAsBlocks',
    'ComfortWFailure',
    'GoesWrongIsMyFault',
    'Resistant2ChangeAfterFail',
    'FailureStopTrying',
    'BetterFailurs',
    'Others2knowWhatIdid',
    'PersonalGainsRImportant',
    'TakeCreditofMyTeam',
    'ComfortwConflict',
    'Vulnerable',
    'ConflctLeadsBetOutcms',
    'WantConflictGoAway',
    'ThinkWOActing',
    'UsePeopl',
    'EasilyDistracted',
    'MakeDecWMissInfo',
    'RelationshpsRTx',
    'SocialSitsDrainEnergy',
    'Conversations',
    'PtMyselfUncomfrtSituations'
}


class ItemMapper:
    """
    Handles mapping between assessment items and behavioral constructs.
    Manages item metadata including reverse scoring and construct groupings.
    """
    
    def __init__(self, custom_mapping: Optional[Dict] = None):
        """
        Initialize ItemMapper with construct mappings.
        
        Args:
            custom_mapping: Optional custom item-to-construct mapping
        """
        self.logger = logging.getLogger(__name__)
        self.construct_mapping = CONSTRUCT_MAPPING
        self.item_to_construct = custom_mapping or ITEM_TO_CONSTRUCT
        self.reverse_scored_items = REVERSE_SCORED_ITEMS
        
        # Create reverse mapping (construct to items)
        self.construct_to_items = self._create_construct_to_items_mapping()
        
        self.logger.info(f"ItemMapper initialized with {len(self.item_to_construct)} items "
                        f"across {len(self.construct_mapping)} constructs")
    
    def _create_construct_to_items_mapping(self) -> Dict[str, List[str]]:
        """Create mapping from constructs to their constituent items."""
        construct_items = {}
        for item, construct in self.item_to_construct.items():
            if construct not in construct_items:
                construct_items[construct] = []
            construct_items[construct].append(item)
        return construct_items
    
    def get_construct_for_item(self, item_id: str) -> Optional[str]:
        """
        Get the construct that an item belongs to.
        
        Args:
            item_id: Assessment item identifier
            
        Returns:
            Construct code or None if item not found
        """
        return self.item_to_construct.get(item_id)
    
    def get_construct_name(self, construct_code: str) -> Optional[str]:
        """
        Get the full name for a construct code.
        
        Args:
            construct_code: Short construct code (e.g., 'RT')
            
        Returns:
            Full construct name or None if not found
        """
        return self.construct_mapping.get(construct_code)
    
    def get_items_for_construct(self, construct_code: str) -> List[str]:
        """
        Get all items that belong to a specific construct.
        
        Args:
            construct_code: Construct code (e.g., 'RT')
            
        Returns:
            List of item identifiers for the construct
        """
        return self.construct_to_items.get(construct_code, [])
    
    def is_reverse_scored(self, item_id: str) -> bool:
        """
        Check if an item should be reverse-scored.
        
        Args:
            item_id: Assessment item identifier
            
        Returns:
            True if item should be reverse-scored
        """
        return item_id in self.reverse_scored_items
    
    def get_all_constructs(self) -> Dict[str, str]:
        """
        Get all available constructs with their full names.
        
        Returns:
            Dictionary mapping construct codes to full names
        """
        return self.construct_mapping.copy()
    
    def get_all_items(self) -> List[str]:
        """
        Get list of all mapped assessment items.
        
        Returns:
            List of all item identifiers
        """
        return list(self.item_to_construct.keys())
    
    def validate_item_coverage(self, items_in_data: List[str]) -> Dict[str, List[str]]:
        """
        Validate that all expected items are present in data.
        
        Args:
            items_in_data: List of items found in actual data
            
        Returns:
            Dictionary with 'missing' and 'unmapped' item lists
        """
        expected_items = set(self.item_to_construct.keys())
        data_items = set(items_in_data)
        
        missing_items = list(expected_items - data_items)
        unmapped_items = list(data_items - expected_items)
        
        if missing_items:
            self.logger.warning(f"Missing {len(missing_items)} expected items: {missing_items[:5]}...")
        
        if unmapped_items:
            self.logger.warning(f"Found {len(unmapped_items)} unmapped items: {unmapped_items[:5]}...")
        
        return {
            'missing': missing_items,
            'unmapped': unmapped_items
        }
    
    def get_construct_statistics(self) -> Dict[str, Dict]:
        """
        Get statistics about construct composition.
        
        Returns:
            Dictionary with statistics for each construct
        """
        stats = {}
        
        for construct_code, construct_name in self.construct_mapping.items():
            items = self.get_items_for_construct(construct_code)
            reverse_items = [item for item in items if self.is_reverse_scored(item)]
            
            stats[construct_code] = {
                'name': construct_name,
                'total_items': len(items),
                'reverse_scored_items': len(reverse_items),
                'items': items
            }
        
        return stats
    
    def export_mapping_csv(self, filepath: str):
        """
        Export the item-to-construct mapping as a CSV file.
        
        Args:
            filepath: Path to save the CSV file
        """
        mapping_data = []
        
        for item_id, construct_code in self.item_to_construct.items():
            mapping_data.append({
                'Item_ID': item_id,
                'Construct_Code': construct_code,
                'Construct_Name': self.get_construct_name(construct_code),
                'Reverse_Scored': self.is_reverse_scored(item_id)
            })
        
        df = pd.DataFrame(mapping_data)
        df.to_csv(filepath, index=False)
        
        self.logger.info(f"Item mapping exported to {filepath}")


# Utility function for easy access
def get_item_mapper() -> ItemMapper:
    """Get a configured ItemMapper instance."""
    return ItemMapper()


if __name__ == "__main__":
    # Demo usage
    mapper = ItemMapper()
    
    print("Construct Statistics:")
    stats = mapper.get_construct_statistics()
    for code, info in stats.items():
        print(f"{code} ({info['name']}): {info['total_items']} items, "
              f"{info['reverse_scored_items']} reverse-scored")
    
    print(f"\nTotal items mapped: {len(mapper.get_all_items())}")
    print(f"Total constructs: {len(mapper.get_all_constructs())}")