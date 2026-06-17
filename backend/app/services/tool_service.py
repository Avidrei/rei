import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from app.config import settings

class UniversalDataToolKit:
    def _get_active_file(self) -> str:
        """Finds the most recently modified or uploaded data asset inside storage."""
        files = [f for f in os.listdir(settings.UPLOAD_DIR) if f.endswith(('.csv', '.txt'))]
        if not files:
            return ""
        # Sort based on timestamp to locate active sheet
        files.sort(key=lambda x: os.path.getmtime(os.path.join(settings.UPLOAD_DIR, x)), reverse=True)
        return files[0]

    def profile_dataset(self) -> Dict[str, Any]:
        """Inspects and profiles whatever dataset is currently active."""
        filename = self._get_active_file()
        if not filename or not filename.endswith('.csv'):
            return {"error": "No structured CSV dataset found to profile."}

        df = pd.read_csv(os.path.join(settings.UPLOAD_DIR, filename))
        
        # Auto-discover structural metadata
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

        summary = {}
        for col in numeric_cols:
            summary[col] = {
                "average": float(df[col].mean()) if not df[col].isnull().all() else 0,
                "max_value": float(df[col].max()) if not df[col].isnull().all() else 0,
                "min_value": float(df[col].min()) if not df[col].isnull().all() else 0
            }

        return {
            "active_file": filename,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "discovered_numeric_fields": numeric_cols,
            "discovered_categorical_fields": categorical_cols,
            "numerical_distribution_profiles": summary
        }

    def execute_slice_query(self, column_name: str, operator: str, target_value: Any) -> Dict[str, Any]:
        """Slices, segments, or filters any arbitrary data collection dynamically."""
        filename = self._get_active_file()
        if not filename or not filename.endswith('.csv'):
            return {"error": "No structured dataset mounted to run execution queries against."}

        df = pd.read_csv(os.path.join(settings.UPLOAD_DIR, filename))

        if column_name not in df.columns:
            return {"error": f"Column '{column_name}' missing. Valid selections are: {list(df.columns)}"}

        try:
            # Match data type cast dynamically
            if df[column_name].dtype in [np.int64, np.float64]:
                target_value = float(target_value)

            # Apply safe logical filters
            if operator == "==":
                subset = df[df[column_name] == target_value]
            elif operator == ">":
                subset = df[df[column_name] > target_value]
            elif operator == "<":
                subset = df[df[column_name] < target_value]
            elif operator == "contains":
                subset = df[df[column_name].astype(str).str.contains(str(target_value), case=False)]
            else:
                return {"error": f"Operator '{operator}' not supported by dynamic tool execution pipeline."}

            return {
                "query_executed": f"{column_name} {operator} {target_value}",
                "matches_discovered": len(subset),
                "data_slice": subset.to_dict(orient="records")[:5] # Limit token payload size safely
            }
        except Exception as e:
            return {"error": f"Execution layer failure: {str(e)}"}
        

    def compute_feature_correlation(self, col_x: str, col_y: str) -> Dict[str, Any]:
        """Calculates Pearson correlation metrics dynamically between two numerical properties."""
        if not self._load_df():
            return {"error": "Target data file is missing."}
            
        if col_x not in self.df.columns or col_y not in self.df.columns:
            return {"error": f"Features must belong to active matrix properties: {list(self.df.columns)}"}
            
        try:
            # Drop structural missing cells to protect calculation arrays
            clean_df = self.df[[col_x, col_y]].dropna()
            correlation_coefficient = float(clean_df[col_x].corr(clean_df[col_y]))
            
            # Contextualize strength values
            strength = "weak"
            if abs(correlation_coefficient) > 0.7:
                strength = "strong"
            elif abs(correlation_coefficient) > 0.4:
                strength = "moderate"
                
            return {
                "metric_type": "linear_correlation",
                "variables": {"x": col_x, "y": col_y},
                "pearson_coefficient": correlation_coefficient,
                "analysis_insight": f"There is a {strength} correlation of {correlation_coefficient:.2f} between {col_x} and {col_y}."
            }
        except Exception as e:
            return {"error": f"Statistical tracking fault: {str(e)}"}

    def compute_categorical_distribution(self, column_name: str) -> Dict[str, Any]:
        """Computes percentage distributions and counts for string/categorical groupings."""
        if not self._load_df():
            return {"error": "Target data file is missing."}
            
        if column_name not in self.df.columns:
            return {"error": f"Target column '{column_name}' missing."}
            
        try:
            counts = self.df[column_name].value_counts()
            percentages = self.df[column_name].value_counts(normalize=True) * 100
            
            distribution = {}
            for index in counts.index:
                # Convert index to clean string representation
                key_str = str(index)
                distribution[key_str] = {
                    "raw_count": int(counts[index]),
                    "percentage_share": float(percentages[index])
                }
                
            return {
                "metric_type": "categorical_distribution",
                "target_feature": column_name,
                "breakdown": distribution
            }
        except Exception as e:
            return {"error": f"Distribution tracking fault: {str(e)}"}

# Register singleton instance
tool_service = UniversalDataToolKit()