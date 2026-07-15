IMAGE_PROMPT = """
Analyze the supplied image for an image-gallery website.

Return only one valid JSON object with exactly these fields:

{
  "title": "A clear, useful and natural title",
  "category": "One short category",
  "alt": "Detailed accessible alt text"
}

Rules:

1. Return JSON only.
2. Do not use Markdown.
3. Do not add ```json code fences.
4. Do not add an explanation before or after the JSON.
5. The title should clearly describe the main subject.
6. The category should contain only one concise category.
7. Alt text should describe important visible content.
8. Do not begin alt text with 'image of' or 'picture of'.
9. Mention important visible text when it helps understanding.
10. Do not invent facts that are not visible in the image.

Preferred categories include:

Health
Food
Technology
Education
Finance
Travel
Nature
Motivation
Relationships
Spirituality
Fitness
News
Business
Entertainment
Science
Lifestyle
Other
""".strip()