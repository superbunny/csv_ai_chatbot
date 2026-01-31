# CSV AI Chatbot 📊

An AI-powered web application that lets you chat with your CSV data using natural language. Upload a CSV file, ask questions, generate visualizations, and perform complex data analysis — all through an intuitive conversational interface powered by Google Gemini.

![CSV AI Chatbot](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **AI-Powered Analysis**: Leverages Google Gemini AI for intelligent data insights
- **Dynamic Visualizations**: Generate charts (bar, line, scatter, histogram, box, pie, heatmap)
- **Statistical Summaries**: Get descriptive statistics, correlations, and distributions
- **Custom Python Analysis**: Execute safe pandas operations through natural language
- **Resizable Panels**: Adjust the interface to your preference
- **Conversational Context**: Maintains chat history for follow-up questions
- **Real-time Data Preview**: View your uploaded CSV data instantly
- **Modern UI**: Beautiful, responsive interface with dark mode aesthetics

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Google Gemini API key ([Get one here](https://ai.google.dev/))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/superbunny/csv_ai_chatbot.git
   cd csv_ai_chatbot
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   
   Navigate to `http://localhost:5001`

## 📖 Usage

### 1. Upload CSV File
Click the "Upload CSV" button and select your CSV file (max 100MB)

### 2. Ask Questions
Try questions like:
- "What are the main trends in this dataset?"
- "Show me a bar chart of sales by region"
- "What's the correlation between age and revenue?"
- "Find outliers in the salary column"
- "Calculate the average revenue per month"

### 3. View Results
The AI will:
- Answer your questions with insights
- Generate visualizations when requested
- Provide statistical summaries
- Execute custom data analysis

## 🏗️ Project Structure

```
csv-ai-chatbot/
├── app.py                 # Flask backend server
├── tools.py               # Data analysis tools and function definitions
├── index.html             # Main HTML interface
├── styles.css             # Styling and UI design
├── script.js              # Frontend JavaScript logic
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── .gitignore            # Git ignore file
├── uploads/              # Uploaded CSV files (auto-created)
├── visualizations/       # Generated chart images (auto-created)
└── README.md             # This file
```

## 🔧 Technology Stack

### Backend
- **Flask**: Web framework
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Matplotlib/Seaborn**: Data visualization
- **Google Generative AI (Gemini)**: AI-powered analysis
- **Python-dotenv**: Environment variable management

### Frontend
- **HTML5**: Structure
- **CSS3**: Styling with modern design
- **Vanilla JavaScript**: Interactive functionality
- **Google Material Icons**: Icon library
- **Inter Font**: Typography

## 🎨 Key Features Explained

### AI Function Calling
The chatbot uses Gemini's function calling capability to execute:

1. **dataframe_info()**: Get metadata about the CSV (columns, shape, data types, missing values)
2. **statistical_summary()**: Generate descriptive statistics for numeric columns
3. **python_analysis()**: Execute safe pandas operations
4. **create_visualization()**: Generate various chart types

### Conversational Context
The application maintains chat history, allowing you to:
- Ask follow-up questions
- Reference previous insights
- Build on earlier analysis

### Safe Code Execution
The `python_analysis` function validates code to prevent:
- File system access
- External imports
- Dangerous operations
- System modifications

## 🔒 Security Features

- File type validation (CSV only)
- File size limits (100MB)
- Secure filename handling
- Sandboxed code execution
- Session-based data isolation
- Input sanitization

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload CSV file |
| `/api/chat` | POST | Send chat message and get AI response |
| `/api/viz/<filename>` | GET | Retrieve generated visualization |
| `/api/session/clear` | POST | Clear current session data |
| `/api/health` | GET | Health check endpoint |

## 📝 Example Interactions

**Q**: "What columns are in this dataset?"  
**A**: The AI will use `dataframe_info()` to list all columns and their types.

**Q**: "Show me a histogram of the age column"  
**A**: The AI will use `create_visualization()` to generate a histogram.

**Q**: "What's the average salary by department?"  
**A**: The AI will use `python_analysis()` to group and calculate averages.

**Q**: "Find the correlation between price and quantity"  
**A**: The AI will use `statistical_summary()` to compute correlations.

## 🛠️ Development

### Running in Development Mode
The app runs in debug mode by default:
```bash
python app.py
```

### Adding New Analysis Tools
To add custom analysis functions:

1. Add the function to the `DataFrameAnalyzer` class in `tools.py`
2. Add the corresponding tool definition to the `TOOLS` list
3. Add the function call handler in `app.py` chat endpoint

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini AI for powering the intelligent analysis
- Flask framework for the backend infrastructure
- Material Icons for the beautiful UI elements

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Note**: This application requires a valid Google Gemini API key. Sign up at [Google AI Studio](https://ai.google.dev/) to get your free API key.

**Happy Data Exploring! 🎉**
