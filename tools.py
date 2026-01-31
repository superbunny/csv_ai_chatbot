"""
Analysis tools for CSV Chatbot that can be called by Gemini function calling.
These functions operate on pandas DataFrames and return JSON-serializable results.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import json
import ast
import os
from typing import Dict, Any, List

# Set seaborn style
sns.set_theme(style="darkgrid")

class DataFrameAnalyzer:
    """Analyzer class that holds DataFrame state and provides analysis tools."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.viz_counter = 0
        
    def dataframe_info(self) -> Dict[str, Any]:
        """
        Get metadata about the DataFrame including columns, shape, data types, and missing values.
        
        Returns:
            Dictionary with DataFrame metadata
        """
        info = {
            "shape": {
                "rows": int(self.df.shape[0]),
                "columns": int(self.df.shape[1])
            },
            "columns": list(self.df.columns),
            "dtypes": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
            "missing_values": {
                col: int(self.df[col].isna().sum()) 
                for col in self.df.columns
            },
            "total_missing": int(self.df.isna().sum().sum()),
            "memory_usage_mb": float(self.df.memory_usage(deep=True).sum() / (1024 * 1024))
        }
        return info
    
    def statistical_summary(self, columns: List[str] = None) -> Dict[str, Any]:
        """
        Generate descriptive statistics for numeric columns.
        
        Args:
            columns: Optional list of column names to summarize. If None, all numeric columns.
            
        Returns:
            Dictionary with statistical summaries
        """
        if columns:
            df_subset = self.df[columns]
        else:
            df_subset = self.df.select_dtypes(include=[np.number])
        
        if df_subset.empty:
            return {"error": "No numeric columns found"}
        
        summary = df_subset.describe().to_dict()
        
        # Add additional statistics
        result = {
            "describe": summary,
            "correlations": df_subset.corr().to_dict() if len(df_subset.columns) > 1 else {},
            "skewness": df_subset.skew().to_dict(),
            "kurtosis": df_subset.kurtosis().to_dict()
        }
        
        return result
    
    def python_analysis(self, code: str) -> Dict[str, Any]:
        """
        Execute pandas code safely on the DataFrame.
        
        Args:
            code: Python code string to execute (should reference 'df')
            
        Returns:
            Dictionary with execution results
        """
        # Security: Parse and validate code
        try:
            parsed = ast.parse(code)
        except SyntaxError as e:
            return {"error": f"Syntax error in code: {str(e)}"}
        
        # Check for dangerous operations
        dangerous_keywords = ['import', 'exec', 'eval', '__', 'open', 'file', 'input', 'compile']
        code_lower = code.lower()
        for keyword in dangerous_keywords:
            if keyword in code_lower:
                return {"error": f"Forbidden operation detected: {keyword}"}
        
        # Execute code in restricted namespace
        try:
            local_vars = {'df': self.df, 'pd': pd, 'np': np}
            exec(code, {"__builtins__": {}}, local_vars)
            
            # Get the result (last variable or modified df)
            if 'result' in local_vars:
                result = local_vars['result']
            else:
                result = local_vars['df']
            
            # Convert result to JSON-serializable format
            if isinstance(result, pd.DataFrame):
                return {
                    "type": "dataframe",
                    "data": result.head(10).to_dict('records'),
                    "shape": list(result.shape)
                }
            elif isinstance(result, pd.Series):
                return {
                    "type": "series",
                    "data": result.head(10).to_dict()
                }
            elif isinstance(result, (int, float, str, bool)):
                return {
                    "type": "scalar",
                    "value": result
                }
            elif isinstance(result, (list, dict)):
                return {
                    "type": "collection",
                    "value": result
                }
            else:
                return {
                    "type": "other",
                    "value": str(result)
                }
                
        except Exception as e:
            return {"error": f"Execution error: {str(e)}"}
    
    def create_visualization(
        self,
        viz_type: str,
        x_column: str = None,
        y_column: str = None,
        title: str = None,
        color_column: str = None,
        aggregation: str = "sum"
    ) -> Dict[str, Any]:
        """
        Create a matplotlib/seaborn chart and save it.
        
        Args:
            viz_type: Type of visualization (bar, line, scatter, histogram, heatmap, box, pie)
            x_column: Column for x-axis
            y_column: Column for y-axis (or value for pie chart)
            title: Chart title
            color_column: Column for color encoding
            aggregation: Aggregation function for grouped data (sum, mean, count, etc.)
            
        Returns:
            Dictionary with visualization file path
        """
        try:
            # Create visualizations directory if it doesn't exist
            viz_dir = "visualizations"
            os.makedirs(viz_dir, exist_ok=True)
            
            # Generate filename
            self.viz_counter += 1
            filename = f"viz_{self.viz_counter}.png"
            filepath = os.path.join(viz_dir, filename)
            
            # Create figure with dark theme
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create visualization based on type
            if viz_type == "bar":
                if y_column:
                    data = self.df.groupby(x_column)[y_column].agg(aggregation)
                    data.plot(kind='bar', ax=ax, color='#5B9FFF')
                else:
                    self.df[x_column].value_counts().plot(kind='bar', ax=ax, color='#5B9FFF')
                    
            elif viz_type == "line":
                if y_column:
                    self.df.plot(x=x_column, y=y_column, kind='line', ax=ax, color='#5B9FFF')
                else:
                    self.df[x_column].plot(kind='line', ax=ax, color='#5B9FFF')
                    
            elif viz_type == "scatter":
                if not y_column:
                    return {"error": "Scatter plot requires both x and y columns"}
                if color_column:
                    self.df.plot(x=x_column, y=y_column, kind='scatter', c=color_column, 
                               cmap='viridis', ax=ax)
                else:
                    self.df.plot(x=x_column, y=y_column, kind='scatter', ax=ax, color='#5B9FFF')
                    
            elif viz_type == "histogram":
                self.df[x_column].plot(kind='hist', bins=30, ax=ax, color='#5B9FFF', alpha=0.7)
                
            elif viz_type == "box":
                if y_column:
                    sns.boxplot(data=self.df, x=x_column, y=y_column, ax=ax, color='#5B9FFF')
                else:
                    sns.boxplot(data=self.df[x_column], ax=ax, color='#5B9FFF')
                    
            elif viz_type == "pie":
                if y_column:
                    data = self.df.groupby(x_column)[y_column].sum()
                else:
                    data = self.df[x_column].value_counts()
                data.plot(kind='pie', ax=ax, autopct='%1.1f%%')
                ax.set_ylabel('')
                
            elif viz_type == "heatmap":
                # Correlation heatmap for numeric columns
                numeric_df = self.df.select_dtypes(include=[np.number])
                sns.heatmap(numeric_df.corr(), annot=True, fmt='.2f', ax=ax, cmap='coolwarm')
                
            else:
                return {"error": f"Unsupported visualization type: {viz_type}"}
            
            # Set title
            if title:
                ax.set_title(title, fontsize=14, fontweight='bold')
            else:
                ax.set_title(f"{viz_type.capitalize()} Chart", fontsize=14, fontweight='bold')
            
            # Improve layout
            plt.tight_layout()
            
            # Save figure
            plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#121212')
            plt.close()
            
            return {
                "success": True,
                "filename": filename,
                "path": filepath,
                "url": f"/viz/{filename}"
            }
            
        except Exception as e:
            return {"error": f"Visualization error: {str(e)}"}


# Tool definitions for Gemini function calling
TOOLS = [
    {
        "name": "dataframe_info",
        "description": "Get metadata about the uploaded CSV file including columns, shape, data types, and missing values. Use this when the user asks about the structure or basic information about their data.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "statistical_summary",
        "description": "Generate descriptive statistics (mean, median, std, min, max, etc.) for numeric columns. Includes correlations, skewness, and kurtosis. Use this when user asks for summary stats or wants to understand distributions.",
        "parameters": {
            "type": "object",
            "properties": {
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of specific columns to summarize. If not provided, all numeric columns are summarized."
                }
            },
            "required": []
        }
    },
    {
        "name": "python_analysis",
        "description": "Execute pandas code on the DataFrame. The DataFrame is available as 'df'. Use this for custom queries, filtering, grouping, calculations, etc. Code must be safe (no imports, file operations, or dangerous operations).",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Must reference 'df' for the DataFrame. Return results in a 'result' variable. Example: result = df[df['revenue'] > 10000].groupby('region')['revenue'].sum()"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "create_visualization",
        "description": "Create charts and visualizations (bar, line, scatter, histogram, box, pie, heatmap). Use this when user asks for a chart, graph, plot, or visualization.",
        "parameters": {
            "type": "object",
            "properties": {
                "viz_type": {
                    "type": "string",
                    "enum": ["bar", "line", "scatter", "histogram", "box", "pie", "heatmap"],
                    "description": "Type of visualization to create"
                },
                "x_column": {
                    "type": "string",
                    "description": "Column name for x-axis or grouping variable"
                },
                "y_column": {
                    "type": "string",
                    "description": "Column name for y-axis or value to plot (optional for some chart types)"
                },
                "title": {
                    "type": "string",
                    "description": "Title for the chart (optional)"
                },
                "aggregation": {
                    "type": "string",
                    "enum": ["sum", "mean", "count", "min", "max", "median"],
                    "description": "Aggregation function for grouped data (default: sum)"
                }
            },
            "required": ["viz_type", "x_column"]
        }
    }
]
