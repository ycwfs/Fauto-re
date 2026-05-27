# Full Auto Research

## Overall Design
Designed for multiple users, with front-end and back-end, user management, subscription management(payment methods access), and can be deployed in production environments.

## Work Flow

```
Paper Discover for Ideas (User instructions: keywords, topics, target meeting, journal template.....) (Base on users' zotero collections, need user interface like APP)
arXiv API → arxiv_fetcher.py → data/papers/papers_YYYY-MM-DD.json
                              ↓
                         paper_summarizer.py (agent/llm) → data/summaries/summaries_YYYY-MM-DD.json
                              ↓
                         trend_analyzer.py (agent/llm) → data/analysis/analysis_YYYY-MM-DD.json
                              ↓
                         zotero_upload.py (CLI + Zotero api) → Zotero library
                              ↓
                         weekly_idea.py (CLI + Zotero api) → idea collection

Ideas verifications and Experiments (User instructions: Basic Repo, Ieads, Goals(may from the stage before)) (Base on autoresearch)
                         weekly_ideas
                              ↓
                         Implace the ideas under a basic repo from opensource-codes or from stratch
                              ↓
                         Automatic improvement experiment results by loop
                              ↓
                         Get experiment results for paper writing

Academic paper writing (User instructions: prepared ml-paper-writing skills, GPT-image-2 skills for image drawing)
                         Follow the skills to write papers section by section in Latex, word which match the target meeting, journal template.

```