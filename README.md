## Notion Bookshelf

A set of scripts and GitHub Actions that automate the process of adding books to a Notion database using ISBNs. It fetches metadata, downloads covers, publishes pages in Notion using a custom template, and maintains backups of your database.

### Project Structure

```
notion_bookshelf/
├─ books/
│  ├─ new_books/          # JSON files for newly fetched books
│  ├─ covers/             # Downloaded cover images (.jpg)
│  └─ processed_books/    # JSON files for books already published
├─ backups/               # Daily Notion DB snapshots
├─ misc/
│  └─ logo.png            # Project logo or assets
├─ script/
│  ├─ add_isbn.py         # Prompt-based ISBN entry into isbn_input.json
│  ├─ isbn_to_book_json.py# Fetch metadata & download covers
│  ├─ publish_book.py     # Publish new books to Notion & archive JSON
│  └─ backup.py           # Pull entire Notion DB and save snapshot
├─ isbn_input.json        # Input file storing ISBN queue
├─ requirements.txt       # Python dependencies
└─ .github/
   └─ workflows/
      ├─ sync-books.yml   # Dispatch-based pipeline (add → fetch → publish)
      └─ backup.yml       # Scheduled daily backup workflow
```

### Setup

1. **Clone the repo**:

   ```bash
   git clone https://github.com/<your-username>/notion_bookshelf.git
   cd notion_bookshelf
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Environment variables** (local/.env or GitHub Secrets):

   ```dotenv
   NOTION_API_TOKEN=<your_notion_integration_token>
   NOTION_DATABASE_ID=<your_notion_database_id>
   AUTO_BOOK_TEMPLATE_ID=<your_auto_book_template_page_id>
   GITHUB_RAW=https://raw.githubusercontent.com/<your-username>/notion_bookshelf/main
   REPO_PAT=<your_github_personal_access_token>
   OPENAI_API_KEY=<optional_for_AI_summaries>
   ```

### Local Usage

1. **Add an ISBN to the queue**:

   ```bash
   python script/add_isbn.py
   # Follow the prompt to enter a 13-digit ISBN
   ```

2. **Fetch metadata & download covers**:

   ```bash
   python script/isbn_to_book_json.py
   ```

3. **Publish new books to Notion**:

   ```bash
   python script/publish_book.py
   ```

4. **Backup your Notion DB**:

   ```bash
   python script/backup.py
   ```

### GitHub Actions Workflows

- **sync-books.yml**: Triggered manually (`workflow_dispatch`) to:

  1. Generate `isbn_input.json` from input
  2. Fetch metadata & covers
  3. Publish to Notion & archive JSON
  4. Commit & push changes

- **backup.yml**: Runs on schedule (daily) and manually to:

  1. Pull entire Notion database
  2. Save a timestamped snapshot in `backups/`
  3. Commit & push the backup file

### Extending the Workflow

- **WhatsApp Integration** via Twilio for ISBN entry
- **Weekly Reading Digest** posted back into Notion
- **AI Summaries** using OpenAI’s ChatGPT API
- **Error Monitoring** with Sentry or custom notifications

### Contributing

Feel free to open issues or pull requests. Please follow the existing code style and add tests for new functionality.

### VS Code YAML Validation Setup

To get proper IntelliSense and avoid warnings in your `.github/workflows/*.yml` files, install the **YAML** or **GitHub Actions** extension and configure VS Code to use the correct schema:

1. Install the **YAML** extension by Red Hat (or the **GitHub Actions** extension) from the VS Code Marketplace.
2. Open your VS Code settings (JSON) and add:
   ```json
   "yaml.schemas": {
     "https://json.schemastore.org/github-workflow.json": "./.github/workflows/*.yml"
   }
   ```
3. Restart VS Code. Your workflow files will now be validated against the official GitHub Actions schema.

### License

This project is licensed under the MIT License.

