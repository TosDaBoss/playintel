# Training PlayIntel from Your Books

This guide shows how to extract data analysis knowledge from your ePub books and inject it into Alex's reasoning.

## Step 1: Export Books from Books App

Since macOS Books app stores files in a protected format, you need to export them:

1. Open **Books** app on your Mac
2. Select the data analysis books you want to use
3. Right-click → **Export** → Choose a folder (e.g., `~/Desktop/books_export/`)
4. This will create ePub files you can process

## Step 2: Install Dependencies

```bash
cd /Users/tosdaboss/playintel
pip3 install -r books_requirements.txt
```

## Step 3: Run the Training Script

```bash
python3 train_from_books.py ~/Desktop/books_export/
```

**What it does:**
1. Scans all ePub files in the folder
2. Uses Claude to identify which books are about data analysis
3. Extracts key concepts, frameworks, and methodologies
4. Synthesizes everything into a unified knowledge base
5. Saves to: `/Users/tosdaboss/playintel/backend/alex_knowledge_base.txt`

**Note:** This will use Claude API credits. Expect ~$1-3 per book depending on length.

## Step 4: Integrate Knowledge into Alex

Once the knowledge base is generated, you can:

### Option A: Add to System Prompt (Recommended)
Open `/Users/tosdaboss/playintel/backend/main.py` and add the knowledge to Alex's persona:

```python
system_prompt = f"""You are Alex, a senior Steam market analyst...

ANALYTICAL TRAINING:
{open('/Users/tosdaboss/playintel/backend/alex_knowledge_base.txt').read()}

DATABASE SCHEMA:
{get_database_schema()}
...
"""
```

### Option B: Create Separate Knowledge Module
Create a function that loads and formats the knowledge:

```python
def get_analytical_knowledge():
    knowledge_path = Path(__file__).parent / "alex_knowledge_base.txt"
    if knowledge_path.exists():
        return knowledge_path.read_text()
    return ""
```

## Example Output

After training, Alex will internalize concepts like:

- **Regression to the mean** - Outlier games rarely stay outliers
- **Survivorship bias** - Successful games are visible; failed ones disappear
- **Cohort analysis** - Track player behavior over time
- **Statistical significance** - Don't trust small sample sizes
- **Correlation vs causation** - High playtime doesn't always mean quality

These become part of Alex's reasoning without needing to cite sources.

## Tips

1. **Start with 1-2 books** to test the pipeline before processing many
2. **Review the generated knowledge base** before integrating
3. **Keep it focused** - Only include books directly relevant to data analysis
4. **Update periodically** - Re-run when you add new books

## Troubleshooting

**Books app won't export?**
- Try copying books to another device first, then exporting
- Or use Calibre to convert Books library to ePub

**Script crashes on a book?**
- Some ePubs have DRM protection - skip those
- Very large books might need chunking adjustments

**Knowledge base too generic?**
- Adjust the synthesis prompt to focus more on gaming/market analysis
- Add domain-specific examples to the prompt

## What NOT to Include

Avoid feeding Alex:
- Fiction books
- General business books (unless data-focused)
- Programming tutorials (unless statistical)
- Marketing books (unless analytics-focused)

Focus on: Statistics, analytics, data science, decision-making frameworks.
