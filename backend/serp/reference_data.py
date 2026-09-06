"""Reference data every install needs, demo data aside.

Region and Language are foreign lookups the add-project and add-keyword forms
cannot render without. They used to live in scripts/seed_local.py, which also
creates the demo account whose password is published in this repository -- so
the one switch that correctly disables that account in production also left
every production install with an empty country list and no way to create a
project. Reference data and demo data do not share a switch.

`manage.py load_reference_data` writes these; the seed imports the same list.

region_name holds the GOOGLE DOMAIN, not the country. The add-keyword form
stores whatever is in region_name on the keyword, and the engine only accepts
a value starting "google." -- anything else silently falls back to google.com,
searching the wrong engine while the UI names the right country.
"""

SEARCH_REGIONS = [
    ('in', 'google.co.in', 'India'),
    ('us', 'google.com', 'United States'),
    ('gb', 'google.co.uk', 'United Kingdom'),
    ('ca', 'google.ca', 'Canada'),
    ('au', 'google.com.au', 'Australia'),
    ('de', 'google.de', 'Germany'),
    ('fr', 'google.fr', 'France'),
    ('es', 'google.es', 'Spain'),
    ('it', 'google.it', 'Italy'),
    ('nl', 'google.nl', 'Netherlands'),
    ('se', 'google.se', 'Sweden'),
    ('pl', 'google.pl', 'Poland'),
    ('br', 'google.com.br', 'Brazil'),
    ('mx', 'google.com.mx', 'Mexico'),
    ('ar', 'google.com.ar', 'Argentina'),
    ('jp', 'google.co.jp', 'Japan'),
    ('kr', 'google.co.kr', 'South Korea'),
    ('sg', 'google.com.sg', 'Singapore'),
    ('id', 'google.co.id', 'Indonesia'),
    ('ph', 'google.com.ph', 'Philippines'),
    ('my', 'google.com.my', 'Malaysia'),
    ('th', 'google.co.th', 'Thailand'),
    ('vn', 'google.com.vn', 'Vietnam'),
    ('ae', 'google.ae', 'United Arab Emirates'),
    ('sa', 'google.com.sa', 'Saudi Arabia'),
    ('za', 'google.co.za', 'South Africa'),
    ('ng', 'google.com.ng', 'Nigeria'),
    ('ke', 'google.co.ke', 'Kenya'),
    ('eg', 'google.com.eg', 'Egypt'),
    ('tr', 'google.com.tr', 'Turkey'),
    ('ru', 'google.ru', 'Russia'),
    ('ua', 'google.com.ua', 'Ukraine'),
    ('il', 'google.co.il', 'Israel'),
    ('pk', 'google.com.pk', 'Pakistan'),
    ('bd', 'google.com.bd', 'Bangladesh'),
    ('lk', 'google.lk', 'Sri Lanka'),
    ('nz', 'google.co.nz', 'New Zealand'),
    ('ie', 'google.ie', 'Ireland'),
    ('pt', 'google.pt', 'Portugal'),
    ('be', 'google.be', 'Belgium'),
    ('ch', 'google.ch', 'Switzerland'),
    ('at', 'google.at', 'Austria'),
    ('dk', 'google.dk', 'Denmark'),
    ('no', 'google.no', 'Norway'),
    ('fi', 'google.fi', 'Finland'),
    ('cz', 'google.cz', 'Czechia'),
    ('gr', 'google.gr', 'Greece'),
    ('hk', 'google.com.hk', 'Hong Kong'),
    ('tw', 'google.com.tw', 'Taiwan'),
    ('cl', 'google.cl', 'Chile'),
    ('co', 'google.com.co', 'Colombia'),
]

# Keyed on language_name, NOT language_code: the form submits the bracketed
# label "(English)" while other code looks up "English", so both rows exist
# and share code "en". Keying on the code would match two rows and raise
# MultipleObjectsReturned on every boot.
LANGUAGES = [
    ("English", "en"),
    ("(English)", "en"),
]
