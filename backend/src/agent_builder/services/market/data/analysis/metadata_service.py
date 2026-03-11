#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Metadata Analysis Service

AI-Native dataset analysis with semantic types, quality scores, and insights.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from loguru import logger


class EnhancedMetadataService:
    """Enhanced Metadata Analysis Service"""
    
    def __init__(self):
        logger.info("Enhanced Metadata Service initialized")
    
    async def analyze_dataset(
        self,
        dataset_id: str,
        dataframe: pd.DataFrame,
        sample_size: int = 1000
    ) -> Dict[str, Any]:
        """Comprehensive dataset analysis"""
        logger.info(f"Analyzing dataset: {dataset_id}")
        
        sample_df = dataframe.head(sample_size) if len(dataframe) > sample_size else dataframe
        
        # 1. Basic statistics
        basic_stats = self._analyze_basic_statistics(sample_df, dataframe)
        
        # 2. Column semantics
        column_semantics = self._analyze_column_semantics(sample_df)
        
        # 3. Distributions
        distributions = self._analyze_distributions(sample_df)
        
        # 4. Quality score
        quality_score = self._calculate_quality_score(dataframe)
        
        # 5. Data understanding
        understanding = self._generate_data_understanding(sample_df, column_semantics)
        
        result = {
            "dataset_id": dataset_id,
            "total_rows": len(dataframe),
            "total_columns": len(dataframe.columns),
            "basic_statistics": basic_stats,
            "column_semantics": column_semantics,
            "distributions": distributions,
            "quality_score": quality_score,
            "data_understanding": understanding,
            "agent_queryable": {
                "quick_summary": self._generate_quick_summary(basic_stats, quality_score),
                "key_fields": self._extract_key_fields(column_semantics)
            }
        }
        
        return result
    
    def _analyze_basic_statistics(self, sample_df: pd.DataFrame, full_df: pd.DataFrame) -> Dict[str, Any]:
        """Basic statistics"""
        stats = {
            "row_count": len(full_df),
            "column_count": len(full_df.columns),
            "memory_usage_mb": full_df.memory_usage(deep=True).sum() / 1024 / 1024,
            "column_types": {},
            "numeric_columns": [],
            "categorical_columns": [],
            "datetime_columns": [],
        }
        
        for col in full_df.columns:
            dtype = str(full_df[col].dtype)
            stats["column_types"][col] = dtype
            
            if pd.api.types.is_numeric_dtype(full_df[col]):
                stats["numeric_columns"].append(col)
            elif pd.api.types.is_datetime64_any_dtype(full_df[col]):
                stats["datetime_columns"].append(col)
            elif full_df[col].dtype == 'object':
                unique_ratio = full_df[col].nunique() / len(full_df[col])
                if unique_ratio < 0.1:
                    stats["categorical_columns"].append(col)
        
        return stats
    
    def _analyze_column_semantics(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Column semantic analysis"""
        semantics = []
        
        for col in df.columns:
            col_info = {
                "name": col,
                "dtype": str(df[col].dtype),
                "semantic_type": self._infer_semantic_type(col),
                "business_description": self._generate_business_description(col),
                "null_count": int(df[col].isnull().sum()),
                "null_ratio": float(df[col].isnull().sum() / len(df[col])),
                "unique_count": int(df[col].nunique()),
            }
            
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info["min"] = float(df[col].min()) if not df[col].isnull().all() else None
                col_info["max"] = float(df[col].max()) if not df[col].isnull().all() else None
                col_info["mean"] = float(df[col].mean()) if not df[col].isnull().all() else None
            
            if df[col].dtype == 'object':
                top_values = df[col].value_counts().head(5)
                col_info["top_values"] = {str(k): int(v) for k, v in top_values.items()}
            
            semantics.append(col_info)
        
        return semantics
    
    def _infer_semantic_type(self, col_name: str) -> str:
        """Infer semantic type from column name"""
        col_lower = col_name.lower()
        
        if any(kw in col_lower for kw in ['id', 'no', 'number', 'code']):
            return "identifier"
        if any(kw in col_lower for kw in ['time', 'date', 'day', 'hour', 'timestamp']):
            return "timestamp"
        if any(kw in col_lower for kw in ['amount', 'price', 'cost', 'money', 'salary', 'revenue', 'profit']):
            return "currency"
        if any(kw in col_lower for kw in ['count', 'num', 'quantity', 'qty', 'total']):
            return "quantity"
        if any(kw in col_lower for kw in ['rate', 'ratio', 'percent', 'percentage']):
            return "percentage"
        if any(kw in col_lower for kw in ['status', 'state', 'flag', 'is_', 'has_', 'enable', 'active']):
            return "status"
        if any(kw in col_lower for kw in ['name', 'title', 'desc', 'description']):
            return "name"
        if any(kw in col_lower for kw in ['type', 'kind', 'category', 'class', 'group', 'level']):
            return "category"
        if any(kw in col_lower for kw in ['city', 'country', 'region', 'province', 'address', 'location']):
            return "location"
        if any(kw in col_lower for kw in ['user', 'customer', 'client', 'member', 'employee']):
            return "user"
        
        return "general"
    
    def _generate_business_description(self, col_name: str) -> str:
        """Generate business description"""
        semantic_type = self._infer_semantic_type(col_name)
        
        descriptions = {
            "identifier": f"{col_name} - Unique identifier",
            "timestamp": f"{col_name} - Timestamp field",
            "currency": f"{col_name} - Currency/amount",
            "quantity": f"{col_name} - Quantity field",
            "percentage": f"{col_name} - Percentage",
            "status": f"{col_name} - Status field",
            "name": f"{col_name} - Name/description",
            "category": f"{col_name} - Category field",
            "location": f"{col_name} - Location info",
            "user": f"{col_name} - User info",
            "general": f"{col_name} - General field"
        }
        
        return descriptions.get(semantic_type, f"{col_name} - General field")
    
    def _analyze_distributions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Data distribution analysis"""
        distributions = {}
        
        for col in df.select_dtypes(include=[np.number]).columns:
            try:
                hist, bin_edges = np.histogram(df[col].dropna(), bins=10)
                distributions[col] = {
                    "type": "histogram",
                    "bins": bin_edges.tolist(),
                    "counts": hist.tolist()
                }
            except:
                pass
        
        return distributions
    
    def _calculate_quality_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate data quality score"""
        total_cells = df.shape[0] * df.shape[1]
        non_null_cells = df.notna().sum().sum()
        
        completeness = non_null_cells / total_cells
        uniqueness = 1 - (df.duplicated().sum() / len(df))
        
        # Simple consistency check
        consistency = 1.0
        type_issues = 0
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    pd.to_numeric(df[col].dropna().head(100))
                    type_issues += 1
                except:
                    pass
        
        if len(df.columns) > 0:
            consistency = 1 - (type_issues / len(df.columns))
        
        overall = (completeness * 0.4 + uniqueness * 0.3 + consistency * 0.3) * 100
        
        return {
            "overall_score": round(overall, 2),
            "completeness": round(completeness * 100, 2),
            "uniqueness": round(uniqueness * 100, 2),
            "consistency": round(consistency * 100, 2),
            "duplicate_rows": int(df.duplicated().sum()),
            "null_cells": int(total_cells - non_null_cells)
        }
    
    def _generate_data_understanding(self, df: pd.DataFrame, column_semantics: List[Dict]) -> Dict[str, Any]:
        """Generate data understanding"""
        row_count = len(df)
        col_count = len(df.columns)
        
        numeric_cols = [c for c in column_semantics if c.get('semantic_type') in ['currency', 'quantity', 'percentage']]
        categorical_cols = [c for c in column_semantics if c.get('semantic_type') in ['category', 'status']]
        
        summary = f"Dataset contains {row_count} rows and {col_count} columns."
        
        suggested_uses = []
        if numeric_cols:
            suggested_uses.extend(["statistical analysis", "machine learning", "prediction"])
        if categorical_cols:
            suggested_uses.extend(["classification analysis", "user segmentation"])
        
        issues = []
        null_ratio = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
        if null_ratio > 0.1:
            issues.append(f"High null ratio ({null_ratio:.1%})")
        
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            issues.append(f"{duplicate_count} duplicate rows")
        
        return {
            "summary": summary,
            "suggested_uses": list(set(suggested_uses)),
            "potential_issues": issues,
        }
    
    def _generate_quick_summary(self, basic_stats: Dict, quality_score: Dict) -> str:
        """Quick summary for Agent"""
        return (
            f"Dataset has {basic_stats['row_count']} rows and {basic_stats['column_count']} columns, "
            f"quality score: {quality_score['overall_score']}/100."
        )
    
    def _extract_key_fields(self, column_semantics: List[Dict]) -> List[Dict]:
        """Extract key fields"""
        key_fields = []
        
        for col in column_semantics:
            if col.get('semantic_type') in ['identifier', 'timestamp', 'currency']:
                key_fields.append({
                    "name": col['name'],
                    "type": col['semantic_type'],
                    "description": col.get('business_description', '')
                })
        
        if len(key_fields) < 3:
            for col in column_semantics[:5]:
                if col['name'] not in [k['name'] for k in key_fields]:
                    key_fields.append({
                        "name": col['name'],
                        "type": col.get('semantic_type', 'general'),
                        "description": col.get('business_description', '')
                    })
        
        return key_fields[:5]


enhanced_metadata_service = EnhancedMetadataService()

__all__ = ['EnhancedMetadataService', 'enhanced_metadata_service']
