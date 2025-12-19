"""
Export Manager - Xuất dữ liệu ra các format khác nhau
CSV, TXT, HTML, JSON
"""
import csv
from typing import List, Dict, Any
from datetime import datetime
from ..core.data_parser import DataParser


class ExportManager:
    """Manager để export data"""
    
    @staticmethod
    def export_to_csv(data_list: List[Dict[str, Any]], filepath: str):
        """
        Export data sang CSV
        Args:
            data_list: list các dict chứa timestamp, direction, data
            filepath: đường dẫn file output
        """
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if not data_list:
                return
            
            fieldnames = ['timestamp', 'direction', 'data_hex', 'data_ascii']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for item in data_list:
                writer.writerow({
                    'timestamp': item.get('timestamp', ''),
                    'direction': item.get('direction', ''),
                    'data_hex': item.get('data', b'').hex(),
                    'data_ascii': DataParser.bytes_to_ascii(item.get('data', b''))
                })
    
    @staticmethod
    def export_to_txt(data_list: List[Dict[str, Any]], filepath: str, 
                     format_type: str = 'hex'):
        """
        Export data sang TXT
        Args:
            data_list: list các dict
            filepath: đường dẫn file
            format_type: 'hex', 'ascii', 'mixed'
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in data_list:
                timestamp = item.get('timestamp', '')
                direction = item.get('direction', '')
                data = item.get('data', b'')
                
                if format_type == 'hex':
                    data_str = DataParser.bytes_to_hex(data)
                elif format_type == 'ascii':
                    data_str = DataParser.bytes_to_ascii(data)
                elif format_type == 'mixed':
                    data_str = DataParser.bytes_to_mixed(data)
                else:
                    data_str = DataParser.bytes_to_hex(data)
                
                line = f"[{timestamp}] {direction}: {data_str}\n"
                f.write(line)
    
    @staticmethod
    def export_to_html(data_list: List[Dict[str, Any]], filepath: str):
        """Export data sang HTML với syntax highlighting"""
        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Serial Monitor Log</title>
    <style>
        body {{
            font-family: 'Consolas', 'Monaco', monospace;
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
        }}
        .log-entry {{
            margin: 5px 0;
            padding: 5px;
            border-left: 3px solid #555;
        }}
        .tx {{
            border-left-color: #4ec9b0;
            background-color: rgba(78, 201, 176, 0.1);
        }}
        .rx {{
            border-left-color: #ce9178;
            background-color: rgba(206, 145, 120, 0.1);
        }}
        .timestamp {{
            color: #858585;
            margin-right: 10px;
        }}
        .direction {{
            font-weight: bold;
            margin-right: 10px;
        }}
        .data {{
            color: #dcdcaa;
        }}
    </style>
</head>
<body>
    <h1>Serial Monitor Log</h1>
    <div class="log-container">
{content}
    </div>
</body>
</html>"""
        
        entries = []
        for item in data_list:
            timestamp = item.get('timestamp', '')
            direction = item.get('direction', 'RX')
            data = item.get('data', b'')
            
            data_hex = DataParser.bytes_to_hex(data)
            data_ascii = DataParser.bytes_to_ascii(data, replace_non_printable=True)
            
            css_class = 'tx' if direction == 'TX' else 'rx'
            
            entry = f'''        <div class="log-entry {css_class}">
            <span class="timestamp">{timestamp}</span>
            <span class="direction">{direction}</span>
            <span class="data">HEX: {data_hex} | ASCII: {data_ascii}</span>
        </div>'''
            entries.append(entry)
        
        content = '\n'.join(entries)
        html = html_template.format(content=content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
    
    @staticmethod
    def export_to_json(data_list: List[Dict[str, Any]], filepath: str):
        """Export data sang JSON"""
        import json
        
        export_data = []
        for item in data_list:
            export_data.append({
                'timestamp': item.get('timestamp', ''),
                'direction': item.get('direction', ''),
                'data_hex': item.get('data', b'').hex(),
                'data_ascii': DataParser.bytes_to_ascii(item.get('data', b''))
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=4, ensure_ascii=False)
    
    @staticmethod
    def import_from_json(filepath: str) -> List[Dict[str, Any]]:
        """Import data từ JSON"""
        import json
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        result = []
        for item in data:
            result.append({
                'timestamp': item.get('timestamp', ''),
                'direction': item.get('direction', ''),
                'data': bytes.fromhex(item.get('data_hex', ''))
            })
        
        return result
