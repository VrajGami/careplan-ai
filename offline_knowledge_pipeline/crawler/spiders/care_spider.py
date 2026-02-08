import scrapy
from urllib.parse import urlparse

class CareSpider(scrapy.Spider):
    name = "care"
    
    # 1. EXPANDED TRUSTED DOMAINS
    allowed_domains = [
        "nice.org.uk",
        "cdc.gov",
        "gov.bc.ca",
        "healthlinkbc.ca",
        "rnao.ca",
        "alz.org",
        "ncoa.org",
        "bgs.org.uk",    # British Geriatrics Society
        "americangeriatrics.org",
        "choosingwisely.org"
    ]
    
    # 2. STRATEGIC ENTRY POINTS
    start_urls = [
        "https://www.healthlinkbc.ca/living-well/getting-older",
        "https://www.cdc.gov/steadi/hcp/index.html",
        "https://www.nice.org.uk/guidance/population-groups/older-people",
        "https://rnao.ca/bpg/guidelines",
        "https://www.bgs.org.uk/resources/resource-series/fit-for-frailty",
        "https://www.alz.org/professionals/care-providers"
    ]

    # 3. CLINICAL BRAIN: Weighted Vocabulary
    CLINICAL_VOCAB = {
        # High Priority: Caregiver Action & Direct Guidance
        "guideline": 10, "bpg": 10, "algorithm": 10, "pathway": 10, 
        "checklist": 8, "nursing-action": 8, "care-plan": 9,
        "intervention": 7, "management": 7, "recommendation": 9,
        
        # Geriatric Syndromes & Fall Focus
        "fall": 5, "frailty": 5, "dementia": 5, "delirium": 5,
        "mobility": 4, "gait": 4, "balance": 4, "hip-fracture": 4,
        "polypharmacy": 6, "medication-review": 6,
        
        # Assessment tools
        "assessment": 5, "tug": 7, "moca": 7, "mmse": 7, "screening": 5,
        "score": 4, "diagnostic": 3
    }

    def parse(self, response):
        # Focus on main content area, ignoring menus/sidebars
        main_content = response.css("main").get() or response.css("article").get() or response.css(".content-area").get()
        
        if main_content:
            yield {
                "url": response.url,
                "html": main_content,
                "domain": urlparse(response.url).netloc,
                "depth": response.meta.get('depth', 0)
            }

        # 4. SMART LINK FILTERING & SCORING
        links = response.css("a::attr(href)").getall()
        scored_links = []

        for link in links:
            absolute_url = response.urljoin(link)
            if not self._is_trusted(absolute_url):
                continue

            score = self._calculate_link_importance(absolute_url)
            if score > 0:
                scored_links.append((absolute_url, score))

        # Sort by score to prioritize high-value guideline pages
        scored_links.sort(key=lambda x: x[1], reverse=True)

        for url, score in scored_links:
            yield response.follow(url, self.parse, meta={'priority': score})

    def _is_trusted(self, url):
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in self.allowed_domains)

    def _calculate_link_importance(self, url):
        """Use 'Smart Brain' logic to determine if a link is worth following."""
        score = 0
        url_lower = url.lower()
        
        # Check against vocabulary
        for term, weight in self.CLINICAL_VOCAB.items():
            if term in url_lower:
                score += weight
        
        # Bonus for PDF (often official guidelines)
        if url_lower.endswith(".pdf"):
            score += 15
            
        # Malware/Ad/Social filter
        if any(bad in url_lower for bad in ["facebook", "twitter", "linkedin", "login", "register", "cart"]):
            return 0
            
        return score
