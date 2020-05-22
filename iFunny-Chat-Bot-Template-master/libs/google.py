import json
from bs4 import BeautifulSoup
import urllib.parse
import requests

header = {'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}

class Images:
	
	@classmethod
	def search(self, query, size=""):

		assert size.lower() in ("l", "m", "s", ""), "Size must be L, M, S, or empty string"

		params = {"q":query,
				  "tbm":"isch",
				  "ijn":0,
				  "start":0,
				  "asearch":"ichunk",
				  "async":"_id:rg_s,_pms:s,_fmt:pc",
				  "safe":"active",
				  "tbs":"isz%3A"+size.lower()}

		url = f"https://www.google.com/search"
		
		soup = BeautifulSoup(requests.get(url, params=params, headers=header, timeout=5).text, "html.parser")
		data = soup.find_all("div", {"class": "rg_meta notranslate"})
		images = [json.loads(i.text) for i in data]
		images = [{"image":{"mime":"image/"+i["ity"],"width":i["ow"],"height":i["oh"],
				  "url":i["ou"]},"thumb":{"mime":"image/"+i["ity"],"width":i["tw"],
				  "height":i["th"],"url":i["tu"]}} for i in images if not i["ou"].startswith("x-raw-image")]

		return images
	
	
	
class Summary:
	
	@classmethod
	def search(self, query):
		
		url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
		html = requests.get(url, headers=header).text
		html = html.replace(u"\xa0", " ")
		soup = BeautifulSoup(html, "html.parser")

		data = {}
		
		snippet = soup.find("div", {"class": "hntNk vk_c vk_bk"})
		snippet2 = soup.find("div", {"class": "ifM9O"})
		snippet3 = soup.find("div", {"class": "vk_c vk_gy vk_sh card-section sL6Rbf"})
		
		if snippet:

			title = snippet.find("div", {"class": "vk_gy vk_sh"})

			if title:

				data["title"] = title.text
				data["description"] = snippet.find("div", {"class": "dDoNo vk_bk"}).text
				
				
		elif snippet3:

			title = snippet3.find("div", {"class": "vk_bk dDoNo"})
			title2 = snippet3.find("div", {"class": "gsrt vk_bk dDoNo"})
			
			if title:
				data["title"] = title.text.strip()
				
			elif title2:
				data["title"] = title2.text.strip()
			
			data["description"] = snippet3.find(class_="vk_gy vk_sh").text.strip()

				
		
		elif snippet2:
			
			title = snippet2.find("div", {"class": "N6Sb2c i29hTd"})
			title2 = snippet2.find("div", {"class": "Z0LcW AZCkJd"})
			description = snippet2.find("div", {"class": "Z0LcW"})
			description2 = snippet2.find("span", {"class": "e24Kjd"})
			has_regular_description = False

			if title or description or description2:
				
				if title:
					data["title"] = title.text

				if description:
					data["description"] = description.text
					has_regular_description = True

				if description2:
					if has_regular_description:
						data["description"] += "\n\n"+description2.text
					else:
						data["description"] = description2.text
				
			elif title2:

				data["title"] = title2.text
				data["description"] = snippet2.find("span", {"class": "e24Kjd"}).text

					
			else:

				title = soup.find("div", {"data-attrid": "title"})

				if title:

					data["title"] = title.text
					subtitle = soup.find("div", {"data-attrid": "subtitle"})

					if subtitle:
						data["subtitle"] = subtitle.text

					description = soup.find("div",{"data-attrid":"description"})

					if description and description.find("span"):
						data["description"] = description.find("span").text


					data["facts"] = {}

					for mod in soup.find_all("div", {"data-md": "1001"}):

						fact_title = mod.find("span",{"class":"w8qArf"})

						if not fact_title: continue

						fact_title = fact_title.text.strip(": ")

						facts = []

						fact_data = mod.find("span",{"class":"LrzXr kno-fv"})
						
						if fact_data:
							
							fact_data_list = fact_data.find_all("a")

							if fact_data_list:
								for item in fact_data_list:
									facts.append(item.text)
							else:
								facts.append(fact_data.text)

							fact_data = ", ".join(facts)

							data["facts"][fact_title] = fact_data

		return data
	

#print(Summary.search("what time is it"))
			

class Translate:
	
	class ISO:

		iso_langs = {
			"ab":{
				"name":"Abkhaz",
				"nativeName":"аҧсуа"
			},
			"aa":{
				"name":"Afar",
				"nativeName":"Afaraf"
			},
			"af":{
				"name":"Afrikaans",
				"nativeName":"Afrikaans"
			},
			"ak":{
				"name":"Akan",
				"nativeName":"Akan"
			},
			"sq":{
				"name":"Albanian",
				"nativeName":"Shqip"
			},
			"am":{
				"name":"Amharic",
				"nativeName":"አማርኛ"
			},
			"ar":{
				"name":"Arabic",
				"nativeName":"العربية"
			},
			"an":{
				"name":"Aragonese",
				"nativeName":"Aragonés"
			},
			"hy":{
				"name":"Armenian",
				"nativeName":"Հայերեն"
			},
			"as":{
				"name":"Assamese",
				"nativeName":"অসমীয়া"
			},
			"av":{
				"name":"Avaric",
				"nativeName":"авар мацӀ, магӀарул мацӀ"
			},
			"ae":{
				"name":"Avestan",
				"nativeName":"avesta"
			},
			"ay":{
				"name":"Aymara",
				"nativeName":"aymar aru"
			},
			"az":{
				"name":"Azerbaijani",
				"nativeName":"azərbaycan dili"
			},
			"bm":{
				"name":"Bambara",
				"nativeName":"bamanankan"
			},
			"ba":{
				"name":"Bashkir",
				"nativeName":"башҡорт теле"
			},
			"eu":{
				"name":"Basque",
				"nativeName":"euskara, euskera"
			},
			"be":{
				"name":"Belarusian",
				"nativeName":"Беларуская"
			},
			"bn":{
				"name":"Bengali",
				"nativeName":"বাংলা"
			},
			"bh":{
				"name":"Bihari",
				"nativeName":"भोजपुरी"
			},
			"bi":{
				"name":"Bislama",
				"nativeName":"Bislama"
			},
			"bs":{
				"name":"Bosnian",
				"nativeName":"bosanski jezik"
			},
			"br":{
				"name":"Breton",
				"nativeName":"brezhoneg"
			},
			"bg":{
				"name":"Bulgarian",
				"nativeName":"български език"
			},
			"my":{
				"name":"Burmese",
				"nativeName":"ဗမာစာ"
			},
			"ca":{
				"name":"Catalan; Valencian",
				"nativeName":"Català"
			},
			"ch":{
				"name":"Chamorro",
				"nativeName":"Chamoru"
			},
			"ce":{
				"name":"Chechen",
				"nativeName":"нохчийн мотт"
			},
			"ny":{
				"name":"Chichewa; Chewa; Nyanja",
				"nativeName":"chiCheŵa, chinyanja"
			},
			"zh":{
				"name":"Chinese",
				"nativeName":"中文 (Zhōngwén), 汉语, 漢語"
			},
			"cv":{
				"name":"Chuvash",
				"nativeName":"чӑваш чӗлхи"
			},
			"kw":{
				"name":"Cornish",
				"nativeName":"Kernewek"
			},
			"co":{
				"name":"Corsican",
				"nativeName":"corsu, lingua corsa"
			},
			"cr":{
				"name":"Cree",
				"nativeName":"ᓀᐦᐃᔭᐍᐏᐣ"
			},
			"hr":{
				"name":"Croatian",
				"nativeName":"hrvatski"
			},
			"cs":{
				"name":"Czech",
				"nativeName":"česky, čeština"
			},
			"da":{
				"name":"Danish",
				"nativeName":"dansk"
			},
			"dv":{
				"name":"Divehi; Dhivehi; Maldivian;",
				"nativeName":"ދިވެހި"
			},
			"nl":{
				"name":"Dutch",
				"nativeName":"Nederlands, Vlaams"
			},
			"en":{
				"name":"English",
				"nativeName":"English"
			},
			"eo":{
				"name":"Esperanto",
				"nativeName":"Esperanto"
			},
			"et":{
				"name":"Estonian",
				"nativeName":"eesti, eesti keel"
			},
			"ee":{
				"name":"Ewe",
				"nativeName":"Eʋegbe"
			},
			"fo":{
				"name":"Faroese",
				"nativeName":"føroyskt"
			},
			"fj":{
				"name":"Fijian",
				"nativeName":"vosa Vakaviti"
			},
			"fi":{
				"name":"Finnish",
				"nativeName":"suomi, suomen kieli"
			},
			"fr":{
				"name":"French",
				"nativeName":"français, langue française"
			},
			"ff":{
				"name":"Fula; Fulah; Pulaar; Pular",
				"nativeName":"Fulfulde, Pulaar, Pular"
			},
			"gl":{
				"name":"Galician",
				"nativeName":"Galego"
			},
			"ka":{
				"name":"Georgian",
				"nativeName":"ქართული"
			},
			"de":{
				"name":"German",
				"nativeName":"Deutsch"
			},
			"el":{
				"name":"Greek, Modern",
				"nativeName":"Ελληνικά"
			},
			"gn":{
				"name":"Guaraní",
				"nativeName":"Avañeẽ"
			},
			"gu":{
				"name":"Gujarati",
				"nativeName":"ગુજરાતી"
			},
			"ht":{
				"name":"Haitian; Haitian Creole",
				"nativeName":"Kreyòl ayisyen"
			},
			"ha":{
				"name":"Hausa",
				"nativeName":"Hausa, هَوُسَ"
			},
			"he":{
				"name":"Hebrew (modern)",
				"nativeName":"עברית"
			},
			"hz":{
				"name":"Herero",
				"nativeName":"Otjiherero"
			},
			"hi":{
				"name":"Hindi",
				"nativeName":"हिन्दी, हिंदी"
			},
			"ho":{
				"name":"Hiri Motu",
				"nativeName":"Hiri Motu"
			},
			"hu":{
				"name":"Hungarian",
				"nativeName":"Magyar"
			},
			"ia":{
				"name":"Interlingua",
				"nativeName":"Interlingua"
			},
			"id":{
				"name":"Indonesian",
				"nativeName":"Bahasa Indonesia"
			},
			"ie":{
				"name":"Interlingue",
				"nativeName":"Originally called Occidental; then Interlingue after WWII"
			},
			"ga":{
				"name":"Irish",
				"nativeName":"Gaeilge"
			},
			"ig":{
				"name":"Igbo",
				"nativeName":"Asụsụ Igbo"
			},
			"ik":{
				"name":"Inupiaq",
				"nativeName":"Iñupiaq, Iñupiatun"
			},
			"io":{
				"name":"Ido",
				"nativeName":"Ido"
			},
			"is":{
				"name":"Icelandic",
				"nativeName":"Íslenska"
			},
			"it":{
				"name":"Italian",
				"nativeName":"Italiano"
			},
			"iu":{
				"name":"Inuktitut",
				"nativeName":"ᐃᓄᒃᑎᑐᑦ"
			},
			"ja":{
				"name":"Japanese",
				"nativeName":"日本語 (にほんご／にっぽんご)"
			},
			"jv":{
				"name":"Javanese",
				"nativeName":"basa Jawa"
			},
			"kl":{
				"name":"Kalaallisut, Greenlandic",
				"nativeName":"kalaallisut, kalaallit oqaasii"
			},
			"kn":{
				"name":"Kannada",
				"nativeName":"ಕನ್ನಡ"
			},
			"kr":{
				"name":"Kanuri",
				"nativeName":"Kanuri"
			},
			"ks":{
				"name":"Kashmiri",
				"nativeName":"कश्मीरी, كشميري‎"
			},
			"kk":{
				"name":"Kazakh",
				"nativeName":"Қазақ тілі"
			},
			"km":{
				"name":"Khmer",
				"nativeName":"ភាសាខ្មែរ"
			},
			"ki":{
				"name":"Kikuyu, Gikuyu",
				"nativeName":"Gĩkũyũ"
			},
			"rw":{
				"name":"Kinyarwanda",
				"nativeName":"Ikinyarwanda"
			},
			"ky":{
				"name":"Kirghiz, Kyrgyz",
				"nativeName":"кыргыз тили"
			},
			"kv":{
				"name":"Komi",
				"nativeName":"коми кыв"
			},
			"kg":{
				"name":"Kongo",
				"nativeName":"KiKongo"
			},
			"ko":{
				"name":"Korean",
				"nativeName":"한국어 (韓國語), 조선말 (朝鮮語)"
			},
			"ku":{
				"name":"Kurdish",
				"nativeName":"Kurdî, كوردی‎"
			},
			"kj":{
				"name":"Kwanyama, Kuanyama",
				"nativeName":"Kuanyama"
			},
			"la":{
				"name":"Latin",
				"nativeName":"latine, lingua latina"
			},
			"lb":{
				"name":"Luxembourgish, Letzeburgesch",
				"nativeName":"Lëtzebuergesch"
			},
			"lg":{
				"name":"Luganda",
				"nativeName":"Luganda"
			},
			"li":{
				"name":"Limburgish, Limburgan, Limburger",
				"nativeName":"Limburgs"
			},
			"ln":{
				"name":"Lingala",
				"nativeName":"Lingála"
			},
			"lo":{
				"name":"Lao",
				"nativeName":"ພາສາລາວ"
			},
			"lt":{
				"name":"Lithuanian",
				"nativeName":"lietuvių kalba"
			},
			"lu":{
				"name":"Luba-Katanga",
				"nativeName":""
			},
			"lv":{
				"name":"Latvian",
				"nativeName":"latviešu valoda"
			},
			"gv":{
				"name":"Manx",
				"nativeName":"Gaelg, Gailck"
			},
			"mk":{
				"name":"Macedonian",
				"nativeName":"македонски јазик"
			},
			"mg":{
				"name":"Malagasy",
				"nativeName":"Malagasy fiteny"
			},
			"ms":{
				"name":"Malay",
				"nativeName":"bahasa Melayu, بهاس ملايو‎"
			},
			"ml":{
				"name":"Malayalam",
				"nativeName":"മലയാളം"
			},
			"mt":{
				"name":"Maltese",
				"nativeName":"Malti"
			},
			"mi":{
				"name":"Māori",
				"nativeName":"te reo Māori"
			},
			"mr":{
				"name":"Marathi (Marāṭhī)",
				"nativeName":"मराठी"
			},
			"mh":{
				"name":"Marshallese",
				"nativeName":"Kajin M̧ajeļ"
			},
			"mn":{
				"name":"Mongolian",
				"nativeName":"монгол"
			},
			"na":{
				"name":"Nauru",
				"nativeName":"Ekakairũ Naoero"
			},
			"nv":{
				"name":"Navajo, Navaho",
				"nativeName":"Diné bizaad, Dinékʼehǰí"
			},
			"nb":{
				"name":"Norwegian Bokmål",
				"nativeName":"Norsk bokmål"
			},
			"nd":{
				"name":"North Ndebele",
				"nativeName":"isiNdebele"
			},
			"ne":{
				"name":"Nepali",
				"nativeName":"नेपाली"
			},
			"ng":{
				"name":"Ndonga",
				"nativeName":"Owambo"
			},
			"nn":{
				"name":"Norwegian Nynorsk",
				"nativeName":"Norsk nynorsk"
			},
			"no":{
				"name":"Norwegian",
				"nativeName":"Norsk"
			},
			"ii":{
				"name":"Nuosu",
				"nativeName":"ꆈꌠ꒿ Nuosuhxop"
			},
			"nr":{
				"name":"South Ndebele",
				"nativeName":"isiNdebele"
			},
			"oc":{
				"name":"Occitan",
				"nativeName":"Occitan"
			},
			"oj":{
				"name":"Ojibwe, Ojibwa",
				"nativeName":"ᐊᓂᔑᓈᐯᒧᐎᓐ"
			},
			"cu":{
				"name":"Old Church Slavonic, Church Slavic, Church Slavonic, Old Bulgarian, Old Slavonic",
				"nativeName":"ѩзыкъ словѣньскъ"
			},
			"om":{
				"name":"Oromo",
				"nativeName":"Afaan Oromoo"
			},
			"or":{
				"name":"Oriya",
				"nativeName":"ଓଡ଼ିଆ"
			},
			"os":{
				"name":"Ossetian, Ossetic",
				"nativeName":"ирон æвзаг"
			},
			"pa":{
				"name":"Panjabi, Punjabi",
				"nativeName":"ਪੰਜਾਬੀ, پنجابی‎"
			},
			"pi":{
				"name":"Pāli",
				"nativeName":"पाऴि"
			},
			"fa":{
				"name":"Persian",
				"nativeName":"فارسی"
			},
			"pl":{
				"name":"Polish",
				"nativeName":"polski"
			},
			"ps":{
				"name":"Pashto, Pushto",
				"nativeName":"پښتو"
			},
			"pt":{
				"name":"Portuguese",
				"nativeName":"Português"
			},
			"qu":{
				"name":"Quechua",
				"nativeName":"Runa Simi, Kichwa"
			},
			"rm":{
				"name":"Romansh",
				"nativeName":"rumantsch grischun"
			},
			"rn":{
				"name":"Kirundi",
				"nativeName":"kiRundi"
			},
			"ro":{
				"name":"Romanian, Moldavian, Moldovan",
				"nativeName":"română"
			},
			"ru":{
				"name":"Russian",
				"nativeName":"русский язык"
			},
			"sa":{
				"name":"Sanskrit (Saṁskṛta)",
				"nativeName":"संस्कृतम्"
			},
			"sc":{
				"name":"Sardinian",
				"nativeName":"sardu"
			},
			"sd":{
				"name":"Sindhi",
				"nativeName":"सिन्धी, سنڌي، سندھی‎"
			},
			"se":{
				"name":"Northern Sami",
				"nativeName":"Davvisámegiella"
			},
			"sm":{
				"name":"Samoan",
				"nativeName":"gagana faa Samoa"
			},
			"sg":{
				"name":"Sango",
				"nativeName":"yângâ tî sängö"
			},
			"sr":{
				"name":"Serbian",
				"nativeName":"српски језик"
			},
			"gd":{
				"name":"Scottish Gaelic; Gaelic",
				"nativeName":"Gàidhlig"
			},
			"sn":{
				"name":"Shona",
				"nativeName":"chiShona"
			},
			"si":{
				"name":"Sinhala, Sinhalese",
				"nativeName":"සිංහල"
			},
			"sk":{
				"name":"Slovak",
				"nativeName":"slovenčina"
			},
			"sl":{
				"name":"Slovene",
				"nativeName":"slovenščina"
			},
			"so":{
				"name":"Somali",
				"nativeName":"Soomaaliga, af Soomaali"
			},
			"st":{
				"name":"Southern Sotho",
				"nativeName":"Sesotho"
			},
			"es":{
				"name":"Spanish; Castilian",
				"nativeName":"español, castellano"
			},
			"su":{
				"name":"Sundanese",
				"nativeName":"Basa Sunda"
			},
			"sw":{
				"name":"Swahili",
				"nativeName":"Kiswahili"
			},
			"ss":{
				"name":"Swati",
				"nativeName":"SiSwati"
			},
			"sv":{
				"name":"Swedish",
				"nativeName":"svenska"
			},
			"ta":{
				"name":"Tamil",
				"nativeName":"தமிழ்"
			},
			"te":{
				"name":"Telugu",
				"nativeName":"తెలుగు"
			},
			"tg":{
				"name":"Tajik",
				"nativeName":"тоҷикӣ, toğikī, تاجیکی‎"
			},
			"th":{
				"name":"Thai",
				"nativeName":"ไทย"
			},
			"ti":{
				"name":"Tigrinya",
				"nativeName":"ትግርኛ"
			},
			"bo":{
				"name":"Tibetan Standard, Tibetan, Central",
				"nativeName":"བོད་ཡིག"
			},
			"tk":{
				"name":"Turkmen",
				"nativeName":"Türkmen, Түркмен"
			},
			"tl":{
				"name":"Tagalog",
				"nativeName":"Wikang Tagalog, ᜏᜒᜃᜅ᜔ ᜆᜄᜎᜓᜄ᜔"
			},
			"tn":{
				"name":"Tswana",
				"nativeName":"Setswana"
			},
			"to":{
				"name":"Tonga (Tonga Islands)",
				"nativeName":"faka Tonga"
			},
			"tr":{
				"name":"Turkish",
				"nativeName":"Türkçe"
			},
			"ts":{
				"name":"Tsonga",
				"nativeName":"Xitsonga"
			},
			"tt":{
				"name":"Tatar",
				"nativeName":"татарча, tatarça, تاتارچا‎"
			},
			"tw":{
				"name":"Twi",
				"nativeName":"Twi"
			},
			"ty":{
				"name":"Tahitian",
				"nativeName":"Reo Tahiti"
			},
			"ug":{
				"name":"Uighur, Uyghur",
				"nativeName":"Uyƣurqə, ئۇيغۇرچە‎"
			},
			"uk":{
				"name":"Ukrainian",
				"nativeName":"українська"
			},
			"ur":{
				"name":"Urdu",
				"nativeName":"اردو"
			},
			"uz":{
				"name":"Uzbek",
				"nativeName":"zbek, Ўзбек, أۇزبېك‎"
			},
			"ve":{
				"name":"Venda",
				"nativeName":"Tshivenḓa"
			},
			"vi":{
				"name":"Vietnamese",
				"nativeName":"Tiếng Việt"
			},
			"vo":{
				"name":"Volapük",
				"nativeName":"Volapük"
			},
			"wa":{
				"name":"Walloon",
				"nativeName":"Walon"
			},
			"cy":{
				"name":"Welsh",
				"nativeName":"Cymraeg"
			},
			"wo":{
				"name":"Wolof",
				"nativeName":"Wollof"
			},
			"fy":{
				"name":"Western Frisian",
				"nativeName":"Frysk"
			},
			"xh":{
				"name":"Xhosa",
				"nativeName":"isiXhosa"
			},
			"yi":{
				"name":"Yiddish",
				"nativeName":"ייִדיש"
			},
			"yo":{
				"name":"Yoruba",
				"nativeName":"Yorùbá"
			},
			"za":{
				"name":"Zhuang, Chuang",
				"nativeName":"Saɯ cueŋƅ, Saw cuengh"
			}
		}

		@classmethod
		def find(self, search):

			search = search.lower()

			if self.iso_langs.get(search):
				return search

			for code, names in self.iso_langs.items():
				name_options = [i.strip() for v in names.values() for i in v.lower().replace(";","").split(",")]
				if search in name_options:
					return code

	@classmethod
	def translate(self, text, source="auto", target="en"):
		
		if source != "auto":
			source = self.ISO.find(source)

		target = self.ISO.find(target)

		if not all((source, target)):
			return "An invalid language was provided"

		limit = 10000
		
		if not text:
			return "Error translating"

		if len(text) > limit:
			return "The translation query is too long to submit"

		query = urllib.parse.quote(text)
		url = f"http://translate.google.com/translate_a/single?dj=1&q={query}&sl={source}&tl={target}&client=at&dt=t"
		header = {'User-Agent':"GoogleTranslate/6.4.0.RC11.286428534 (Linux; U; Android 8.0.0; ONEPLUS A3000)",
				  "Host": "translate.google.com", "accept-encoding": "gzip"}
		data = requests.get(url, headers=header).text
		
		try:
			data = json.loads(data)
		except:
			return text

		translation = text

		if data.get("sentences"):
			translation = "".join([phrase["trans"] for phrase in data["sentences"]])

		return translation
	
