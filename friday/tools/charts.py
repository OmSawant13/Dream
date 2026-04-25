"""
Chart tools — generate ASCII data visualizations for diagnostics.
"""

def register(mcp):

    @mcp.tool()
    def generate_ascii_chart(data: list[float], label: str = "Metric") -> str:
        """
        Creates an ASCII line chart for a list of data points.
        """
        if not data:
            return "No data points provided for visualization, boss."
            
        max_val = max(data)
        min_val = min(data)
        range_val = max_val - min_val if max_val != min_val else 1
        
        height = 5
        chart = [f"### VISUAL DATA: {label.upper()}\n"]
        
        for h in range(height, -1, -1):
            threshold = min_val + (range_val * h / height)
            line = [f"{threshold:6.1f} | "]
            for val in data:
                if val >= threshold:
                    line.append("█")
                else:
                    line.append(" ")
            chart.append("".join(line))
            
        chart.append("       " + "-" * len(data))
        chart.append("       (Time Tracking Active)")
        
        return "\n".join(chart)

    @mcp.tool()
    def show_gauge(value: float, min_v: float = 0, max_v: float = 100) -> str:
        """
        Shows a simple ASCII progress gauge for a single value.
        """
        percent = int((value - min_v) / (max_v - min_v) * 20)
        gauge = "[" + "=" * percent + " " * (20 - percent) + "]"
        return f"{gauge} {value}%"
