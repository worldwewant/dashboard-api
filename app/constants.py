"""
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import json

from app.enums.question_code import QuestionCode

QUESTION_CODES = [q.value for q in QuestionCode]

# Load stopwords from file
with open("stopwords.json", "r", encoding="utf8") as file:
    STOPWORDS: dict = json.loads(file.read())

# Load countries data from file
with open("countries_data.json", "r") as file:
    COUNTRIES_DATA: dict = json.loads(file.read())

# This is nominally the coordinates of the capital of each country
# but where they appear too close together on the map I have shifted them slightly.
# All lat/longs are definitely inside the country that they are supposed to be in,
# but they are sometimes not the capital if that capital is very close to the capital of another country.
COUNTRY_COORDINATE = {}
for key, value in COUNTRIES_DATA.items():
    COUNTRY_COORDINATE[key] = value["coordinates"]

LANGUAGES_GOOGLE = {
    "af": {"name": "Afrikaans"},
    "ak": {"name": "Akan"},
    "am": {"name": "አማርኛ"},
    "ar": {"name": "العربية"},
    "as": {"name": "অসমীয়া"},
    "ay": {"name": "Aymar aru"},
    "az": {"name": "azərbaycan"},
    "be": {"name": "беларуская"},
    "bg": {"name": "български"},
    "bho": {"name": "भोजपुरी"},
    "bm": {"name": "bamanakan"},
    "bn": {"name": "বাংলা"},
    "bs": {"name": "bosanski"},
    "ca": {"name": "català"},
    "ceb": {"name": "Binisaya"},
    "ckb": {"name": "کوردیی ناوەندی"},
    "co": {"name": "corsu"},
    "cs": {"name": "čeština"},
    "cy": {"name": "Cymraeg"},
    "da": {"name": "dansk"},
    "de": {"name": "Deutsch"},
    "doi": {"name": "डोगरी"},
    "dv": {"name": "ދިވެހި"},
    "ee": {"name": "Eʋegbe"},
    "el": {"name": "Ελληνικά"},
    "en": {"name": "English"},
    "eo": {"name": "esperanto"},
    "es": {"name": "español"},
    "et": {"name": "eesti"},
    "eu": {"name": "euskara"},
    "fa": {"name": "فارسی"},
    "fi": {"name": "suomi"},
    "fil": {"name": "Filipino"},
    "fr": {"name": "français"},
    "fy": {"name": "Frysk"},
    "ga": {"name": "Gaeilge"},
    "gd": {"name": "Gàidhlig"},
    "gl": {"name": "galego"},
    "gn": {"name": "Avañeʼẽ"},
    "gom": {"name": "कोंकणी"},
    "gu": {"name": "ગુજરાતી"},
    "ha": {"name": "Hausa"},
    "haw": {"name": "ʻŌlelo Hawaiʻi"},
    "he": {"name": "עברית"},
    "hi": {"name": "हिन्दी"},
    "hmn": {"name": "lus Hmoob"},
    "hr": {"name": "hrvatski"},
    "ht": {"name": "kreyòl ayisyen"},
    "hu": {"name": "magyar"},
    "hy": {"name": "հայերեն"},
    "id": {"name": "Indonesia"},
    "ig": {"name": "Asụsụ Igbo"},
    "ilo": {"name": "Ilokano"},
    "is": {"name": "íslenska"},
    "it": {"name": "italiano"},
    "ja": {"name": "日本語"},
    "jv": {"name": "Jawa"},
    "ka": {"name": "ქართული"},
    "kk": {"name": "қазақ тілі"},
    "km": {"name": "ខ្មែរ"},
    "kn": {"name": "ಕನ್ನಡ"},
    "ko": {"name": "한국어"},
    "kri": {"name": "Krio"},
    "ku": {"name": "kurdî"},
    "ky": {"name": "кыргызча"},
    "la": {"name": "Lingua Latīna"},
    "lb": {"name": "Lëtzebuergesch"},
    "lg": {"name": "Luganda"},
    "ln": {"name": "lingála"},
    "lo": {"name": "ລາວ"},
    "lt": {"name": "lietuvių"},
    "lus": {"name": "Mizo ṭawng"},
    "lv": {"name": "latviešu"},
    "mai": {"name": "मैथिली"},
    "mg": {"name": "Malagasy"},
    "mi": {"name": "Māori"},
    "mk": {"name": "македонски"},
    "ml": {"name": "മലയാളം"},
    "mn": {"name": "монгол"},
    "mni_mtei": {"name": "ꯃꯩꯇꯩꯂꯣꯟ"},
    "mr": {"name": "मराठी"},
    "ms": {"name": "Melayu"},
    "mt": {"name": "Malti"},
    "my": {"name": "မြန်မာ"},
    "ne": {"name": "नेपाली"},
    "nl": {"name": "Nederlands"},
    "no": {"name": "norsk"},
    "nso": {"name": "Sepedi"},
    "ny": {"name": "Chichewa"},
    "om": {"name": "Oromoo"},
    "or": {"name": "ଓଡ଼ିଆ"},
    "pa": {"name": "ਪੰਜਾਬੀ"},
    "pl": {"name": "polski"},
    "ps": {"name": "پښتو"},
    "pt": {"name": "português"},
    "qu": {"name": "Runasimi"},
    "ro": {"name": "română"},
    "ru": {"name": "русский"},
    "rw": {"name": "Kinyarwanda"},
    "sa": {"name": "संस्कृत"},
    "sd": {"name": "سنڌي"},
    "si": {"name": "සිංහල"},
    "sk": {"name": "slovenčina"},
    "sl": {"name": "slovenščina"},
    "sm": {"name": "Gagana faʻa Sāmoa"},
    "sn": {"name": "chiShona"},
    "so": {"name": "Soomaali"},
    "sq": {"name": "shqip"},
    "sr": {"name": "српски"},
    "st": {"name": "Sesotho"},
    "su": {"name": "Basa Sunda"},
    "sv": {"name": "svenska"},
    "sw": {"name": "Kiswahili"},
    "ta": {"name": "தமிழ்"},
    "te": {"name": "తెలుగు"},
    "tg": {"name": "тоҷикӣ"},
    "th": {"name": "ไทย"},
    "ti": {"name": "ትግርኛ"},
    "tk": {"name": "türkmen dili"},
    "tl": {"name": "Tagalog"},
    "tr": {"name": "Türkçe"},
    "ts": {"name": "Xitsonga"},
    "tt": {"name": "татар"},
    "ug": {"name": "ئۇيغۇرچە"},
    "uk": {"name": "українська"},
    "ur": {"name": "اردو"},
    "uz": {"name": "o‘zbek"},
    "vi": {"name": "Tiếng Việt"},
    "xh": {"name": "isiXhosa"},
    "yi": {"name": "ייִדיש"},
    "yo": {"name": "Èdè Yorùbá"},
    "zh": {"name": "中国人"},
    "zh_tw": {"name": "中國人"},
    "zu": {"name": "isiZulu"},
}

LANGUAGES_AZURE = {
    "af": {"name": "Afrikaans"},
    "sq": {"name": "shqip"},
    "am": {"name": "አማርኛ"},
    "ar": {"name": "العربية"},
    "hy": {"name": "հայերեն"},
    "as": {"name": "অসমীয়া"},
    "az": {"name": "azərbaycan"},
    "bn": {"name": "বাংলা"},
    "ba": {"name": "Bashkir"},
    "eu": {"name": "euskara"},
    "bho": {"name": "भोजपुरी"},
    "brx": {"name": "Bodo"},
    "bs": {"name": "bosanski"},
    "bg": {"name": "български"},
    "yue": {"name": "Cantonese (Traditional)"},
    "ca": {"name": "català"},
    "lzh": {"name": "Chinese (Literary)"},
    "zh-Hans": {"name": "Chinese Simplified"},
    "zh-Hant": {"name": "Chinese Traditional"},
    "sn": {"name": "chiShona"},
    "hr": {"name": "hrvatski"},
    "cs": {"name": "čeština"},
    "da": {"name": "dansk"},
    "prs": {"name": "Dari"},
    "dv": {"name": "ދިވެހި"},
    "doi": {"name": "डोगरी"},
    "nl": {"name": "Nederlands"},
    "en": {"name": "English"},
    "et": {"name": "eesti"},
    "fo": {"name": "Faroese"},
    "fj": {"name": "Fijian"},
    "fil": {"name": "Filipino"},
    "fi": {"name": "suomi"},
    "fr": {"name": "français"},
    "fr-ca": {"name": "French (Canada)"},
    "gl": {"name": "galego"},
    "ka": {"name": "ქართული"},
    "de": {"name": "Deutsch"},
    "el": {"name": "Ελληνικά"},
    "gu": {"name": "ગુજરાતી"},
    "ht": {"name": "kreyòl ayisyen"},
    "ha": {"name": "Hausa"},
    "he": {"name": "עברית"},
    "hi": {"name": "हिन्दी"},
    "mww": {"name": "Hmong Daw (Latin)"},
    "hu": {"name": "magyar"},
    "is": {"name": "íslenska"},
    "ig": {"name": "Asụsụ Igbo"},
    "id": {"name": "Indonesia"},
    "ikt": {"name": "Inuinnaqtun"},
    "iu": {"name": "Inuktitut"},
    "iu-Latn": {"name": "Inuktitut (Latin)"},
    "ga": {"name": "Gaeilge"},
    "it": {"name": "italiano"},
    "ja": {"name": "日本語"},
    "kn": {"name": "ಕನ್ನಡ"},
    "ks": {"name": "Kashmiri"},
    "kk": {"name": "қазақ тілі"},
    "km": {"name": "ខ្មែរ"},
    "rw": {"name": "Kinyarwanda"},
    "tlh-Latn": {"name": "Klingon"},
    "tlh-Piqd": {"name": "Klingon (plqaD)"},
    "gom": {"name": "कोंकणी"},
    "ko": {"name": "한국어"},
    "ku": {"name": "kurdî"},
    "kmr": {"name": "Kurdish (Northern)"},
    "ky": {"name": "кыргызча"},
    "lo": {"name": "ລາວ"},
    "lv": {"name": "latviešu"},
    "lt": {"name": "lietuvių"},
    "ln": {"name": "lingála"},
    "dsb": {"name": "Lower Sorbian"},
    "lug": {"name": "Luganda"},
    "mk": {"name": "македонски"},
    "mai": {"name": "मैथिली"},
    "mg": {"name": "Malagasy"},
    "ms": {"name": "Melayu"},
    "ml": {"name": "മലയാളം"},
    "mt": {"name": "Malti"},
    "mi": {"name": "Māori"},
    "mr": {"name": "मराठी"},
    "mn-Cyrl": {"name": "Mongolian (Cyrillic)"},
    "mn-Mong": {"name": "Mongolian (Traditional)"},
    "my": {"name": "မြန်မာ"},
    "ne": {"name": "नेपाली"},
    "nb": {"name": "Norwegian"},
    "nya": {"name": "Nyanja"},
    "or": {"name": "ଓଡ଼ିଆ"},
    "ps": {"name": "پښتو"},
    "fa": {"name": "فارسی"},
    "pl": {"name": "polski"},
    "pt": {"name": "português"},
    "pt-pt": {"name": "Portuguese (Portugal)"},
    "pa": {"name": "ਪੰਜਾਬੀ"},
    "otq": {"name": "Queretaro Otomi"},
    "ro": {"name": "română"},
    "run": {"name": "Rundi"},
    "ru": {"name": "русский"},
    "sm": {"name": "Gagana faʻa Sāmoa"},
    "sr-Cyrl": {"name": "Serbian (Cyrillic)"},
    "sr-Latn": {"name": "Serbian (Latin)"},
    "st": {"name": "Sesotho"},
    "nso": {"name": "Sepedi"},
    "tn": {"name": "Setswana"},
    "sd": {"name": "سنڌي"},
    "si": {"name": "සිංහල"},
    "sk": {"name": "slovenčina"},
    "sl": {"name": "slovenščina"},
    "so": {"name": "Soomaali"},
    "es": {"name": "español"},
    "sw": {"name": "Kiswahili"},
    "sv": {"name": "svenska"},
    "ty": {"name": "Tahitian"},
    "ta": {"name": "தமிழ்"},
    "tt": {"name": "татар"},
    "te": {"name": "తెలుగు"},
    "th": {"name": "ไทย"},
    "bo": {"name": "Tibetan"},
    "ti": {"name": "ትግርኛ"},
    "to": {"name": "Tongan"},
    "tr": {"name": "Türkçe"},
    "tk": {"name": "türkmen dili"},
    "uk": {"name": "українська"},
    "hsb": {"name": "Upper Sorbian"},
    "ur": {"name": "اردو"},
    "ug": {"name": "ئۇيغۇرچە"},
    "uz": {"name": "o‘zbek"},
    "vi": {"name": "Tiếng Việt"},
    "cy": {"name": "Cymraeg"},
    "xh": {"name": "isiXhosa"},
    "yo": {"name": "Èdè Yorùbá"},
    "yua": {"name": "Yucatec Maya"},
    "zu": {"name": "isiZulu"},
}

TRANSLATIONS_JSON = "translations.json"
ACCESS_TOKEN_EXPIRE_DAYS = 30
N_WORDCLOUD_WORDS = 100
N_TOP_WORDS = 20
N_RESPONSES_SAMPLE = 1000
