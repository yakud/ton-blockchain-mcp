# TON MCP Server

A Model Context Protocol server for natural language interaction with the TON blockchain.

## Features

- **Natural Language Processing**: Understand complex blockchain queries in plain English
- **Trading Analysis**: Analyze trading patterns, profitability, and strategies
- **Hot Trends Detection**: Find trending tokens, active pools, and high-activity accounts
- **Forensics & Compliance**: Conduct blockchain investigations and compliance checks
- **Real-time Data**: Access live TON blockchain data through TON API

## Quick Start

### Prerequisites

- Python 3.8+
- TON API key from TON

### Installation

1. Clone the repository:
```bash
git clone https://github.com/devonmojito/ton-mcp-server.git
cd ton-mcp-server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export TON_API_KEY=your_api_key_here
```

4. Run the server:
```bash
python -m src.mcp_server
```

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

## Usage

### Basic Queries

```python
import asyncio
from mcp_client import McpClient

async def main():
    client = McpClient("http://localhost:8000")
    
    # Analyze an address
    result = await client.call_tool("analyze_address", {
        "address": "EQD1234...",
        "deep_analysis": True
    })
    print(result)

asyncio.run(main())
```

### Natural Language Examples

- "What's the balance of address EQD1234...?"
- "Find hot trading pairs in the last hour"
- "Analyze trading patterns for this wallet"
- "Show suspicious activity for address ABC"
- "Trace money flow from this address"

## Configuration

Configuration can be provided via:
- Environment variables
- `config/settings.json` file
- Runtime parameters

Key configuration options:
- `TON_API_KEY`: Your TON API key
- `MCP_HOST`: Server host (default: localhost)
- `MCP_PORT`: Server port (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)

## API Documentation

### Tools

#### analyze_address
Analyze a TON address including balance, transactions, and patterns.

**Parameters:**
- `address` (str): TON address to analyze
- `deep_analysis` (bool): Enable deep forensic analysis

#### find_hot_trends
Find hot trends on TON blockchain.

**Parameters:**
- `timeframe` (str): Time period (1h, 24h, 7d)
- `category` (str): Type of trends (tokens, pools, accounts)

#### conduct_forensics
Conduct blockchain forensics investigation.

**Parameters:**
- `target` (str): Address or transaction hash
- `investigation_type` (str): Type of investigation

### Prompts

- `trading_analysis`: Generate trading analysis prompts
- `forensics_investigation`: Generate forensics prompts
- `trend_analysis`: Generate trend analysis prompts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue on GitHub or contact the development team.
```

## Installation and Usage Instructions

1. **Create the project structure**:
```bash
mkdir ton-mcp-server
cd ton-mcp-server
mkdir -p src config examples
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment**:
```bash
export TON_API_KEY=your_ton_api_key
```

5. **Run the server**:
```bash
python -m src.mcp_server
```

6. **Test with example client**:
```bash
python examples/client_example.py
```

This comprehensive TON MCP server provides:

- ✅ Full MCP protocol implementation
- ✅ Natural language query processing
- ✅ TON blockchain data analysis
- ✅ Trading pattern analysis
- ✅ Forensics and compliance tools
- ✅ Hot trends detection
- ✅ Configurable and extensible architecture
- ✅ Docker support
- ✅ Comprehensive documentation

The server is ready to be deployed and can handle complex queries about the TON blockchain using natural language!