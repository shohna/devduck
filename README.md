# Multi-Tool Chat Assistant

This project implements a modular, multi-tool chat assistant that dynamically selects and executes specialized tools based on user queries. The system is designed to support different functionalities (such as internet search, ideation, and therapeutic conversation) by routing each query to the appropriate tool handler using a configurable tool registry and client management.

## Features

- **Dynamic Tool Selection:** An expert decision engine selects the right tool for each query based on available capabilities.
- **Multiple Specialized Tools:**
  - **Internet Search:** Uses the Perplexity API to fetch up-to-date information, news, and facts.
  - **Ideation:** Helps users brainstorm by asking probing questions and guiding the thought process.
  - **Therapist:** Provides empathetic conversation and emotional support tailored to the user's context.
- **Extensible Architecture:** Easily add new tools and API clients by registering them using the provided interfaces.
- **Conversation History Management:** Maintains context across interactions to ensure coherent, context-aware conversations.

## Code Structure

- **`main.py`:**  
  Contains the core implementation:
  - **Tool Class:** A dataclass that encapsulates tool details such as name, description, system prompt, and client type.
  - **ClientManager:** Handles connections with different API clients (e.g., `local`, `perplexity`) and supports registration of additional clients.
  - **BaseTool & Tool Handlers:** Abstract base class and concrete implementations (`InternetSearchTool`, `IdeationTool`, `TherapistTool`) that process user queries.
  - **ToolRegistry:** Maintains the list of tools and formats them for the OpenAI function call style, facilitating dynamic tool selection.
  - **ToolHandler:** Orchestrates tool selection, maintains conversation history, and executes the chosen tool's processing function.
  - **CLI Loop:** A simple command-line interface that accepts user queries and displays tool outputs.

## Setup and Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/multi-tool-chat-assistant.git
   cd multi-tool-chat-assistant
   ```

2. **Set Up a Virtual Environment (Optional but Recommended):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**

   This project requires Python 3.8+ and the following packages:
   - `openai`
   - Other standard libraries (`dataclasses`, `typing`, etc.) which come with Python.

   If you have a `requirements.txt` file, run:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**

   - For the Perplexity API, set the `PERPLEXITY_API_KEY`:
     ```bash
     export PERPLEXITY_API_KEY="your_perplexity_api_key"
     ```
   - Adjust and set additional API keys as needed if you plan to extend the client set (e.g., Anthropic).

## Running the Application

To start the chat assistant, simply run:

```bash
python main.py
```

You will be prompted to enter your query in the terminal. Type `bye` to exit the application.

## Contributing

Contributions are welcome! If you have ideas for new tools, enhancements, or bug fixes, please fork the repository and submit a pull request. For major changes, please open an issue to discuss what you would like to change.

### Steps to Contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes with clear and concise commit messages.
4. Run tests to ensure your changes don't break existing functionality.
5. Submit a pull request with a detailed description of your changes.

## Known Issues and Future Improvements

- **Type Consistency:**  
  Some parts of the conversation history handling may need to be standardized. Future updates will address these areas.
- **Enhanced Error Handling:**  
  Improvements in error handling and logging are planned to increase the robustness of the tool selection and execution processes.
- **Additional Tools and APIs:**  
  The architecture is designed to be extended easily by adding new tools and integrating with other AI services.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or further information, please open an issue in this repository or contact at [your.email@example.com](mailto:your.email@example.com).
