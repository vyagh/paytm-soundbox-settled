# The lines Settled says, keyed by language. Each constant is the English line,
# which is also what the board shows, what the log keeps and the key flow.py
# passes to the listener. LANGUAGES holds what is spoken, in each language's own
# script. {owner}, {salesman}, {price}, {signed} and {starts} come from the
# shop's record, see say().
#
# Hindi is hand-written. Every other language is machine-written and needs a
# native speaker to check it before it goes in front of a real shop. UNCHECKED
# lists them.
#
# The set is every language both Sarvam text-to-speech (bulbul:v3) and
# speech-to-text take, voices from docs.sarvam.ai bulbul-v3 best practices
# (2026-10-31).
from datetime import date

CONSENT = "Namaste, this is Paytm, calling about your Soundbox. This call is being recorded, is that okay?"
NAME_RECORDED = "Thank you. Am I speaking with {owner}?"
NAME_UNRECORDED = "Okay, this call will not be recorded. Am I speaking with {owner}?"
CODE = "To confirm it's you, a 4-digit code has just come on your Paytm app. Please tell me the code."
ASK = "{salesman} gave you the ₹{price} a month plan on {signed}, starting {starts}. Is this the plan you took?"
READ_BACK = "So ₹{price} every month, from {starts}. Shall I confirm it?"
CHARGED = "Thank you. Your plan starts on {starts}, and you will get an SMS too. Have a good day."
FOLLOW_UP = ("Sorry for the trouble. Nothing will be taken now. A Paytm person will call you with the right offer, "
             "and we are sending the details on WhatsApp. Thank you.")
GOODBYE_OTHER = "No problem. Please tell {owner} that Paytm called. We will talk to them later. Thank you."
GOODBYE_UNVERIFIED = ("Sorry, we could not confirm who we are speaking with, so nothing has changed. "
                      "A Paytm person will call the registered number. Thank you.")

LINES = (CONSENT, NAME_RECORDED, NAME_UNRECORDED, CODE, ASK, READ_BACK, CHARGED, FOLLOW_UP, GOODBYE_OTHER, GOODBYE_UNVERIFIED)
# Lines that take no reply: Settled says them and the call goes on or ends.
STATEMENTS = (CHARGED, FOLLOW_UP, GOODBYE_OTHER, GOODBYE_UNVERIFIED)
UNCHECKED = ("bn", "gu", "kn", "ml", "mr", "od", "pa", "ta", "te", "en")

LANGUAGES = {
    "hi": {
        "name": "Hindi", "own": "हिन्दी", "code": "hi-IN", "voice": "shubh",
        "months": "जनवरी फ़रवरी मार्च अप्रैल मई जून जुलाई अगस्त सितंबर अक्टूबर नवंबर दिसंबर",
        CONSENT: "नमस्ते जी, मैं पेटीएम से बोल रहा हूँ, आपके साउंडबॉक्स के बारे में. यह कॉल रिकॉर्ड हो रही है, ठीक है?",
        NAME_RECORDED: "धन्यवाद जी. क्या मैं {owner} जी से बात कर रहा हूँ?",
        NAME_UNRECORDED: "ठीक है, यह कॉल रिकॉर्ड नहीं होगी. क्या मैं {owner} जी से बात कर रहा हूँ?",
        CODE: "पहचान पक्की करने के लिए, आपके पेटीएम ऐप पर अभी एक चार अंकों का कोड आया है. वो कोड बता दीजिए.",
        ASK: "{salesman} ने {signed} को आपको {price} रुपये महीने वाला प्लान दिया था, {starts} से. क्या आपने यही प्लान लिया था?",
        READ_BACK: "तो {starts} से हर महीने {price} रुपये लगेंगे. यह पक्का कर दूँ?",
        CHARGED: "बहुत धन्यवाद. आपका प्लान {starts} से चालू होगा, एसएमएस भी आ जाएगा. आपका दिन शुभ हो.",
        FOLLOW_UP: "माफ़ कीजिए, आपको परेशानी हुई. अभी कुछ नहीं कटेगा. पेटीएम की टीम आपको सही ऑफ़र के साथ कॉल करेगी, और पूरी जानकारी व्हाट्सऐप पर भेज रहे हैं. धन्यवाद.",
        GOODBYE_OTHER: "कोई बात नहीं. {owner} जी को बता दीजिए कि पेटीएम से कॉल आया था, हम उनसे बाद में बात कर लेंगे. धन्यवाद.",
        GOODBYE_UNVERIFIED: "माफ़ कीजिए, हम पहचान पक्की नहीं कर पाए, इसलिए अभी कुछ नहीं बदला है. पेटीएम की टीम रजिस्टर्ड नंबर पर बात करेगी. धन्यवाद.",
    },
    "bn": {
        "name": "Bengali", "own": "বাংলা", "code": "bn-IN", "voice": "rehan",
        "months": "জানুয়ারি ফেব্রুয়ারি মার্চ এপ্রিল মে জুন জুলাই আগস্ট সেপ্টেম্বর অক্টোবর নভেম্বর ডিসেম্বর",
        CONSENT: "নমস্কার, আমি পেটিএম থেকে বলছি, আপনার সাউন্ডবক্সের ব্যাপারে। এই কলটি রেকর্ড হচ্ছে, ঠিক আছে?",
        NAME_RECORDED: "ধন্যবাদ। আমি কি {owner}-এর সাথে কথা বলছি?",
        NAME_UNRECORDED: "ঠিক আছে, এই কলটি রেকর্ড হবে না। আমি কি {owner}-এর সাথে কথা বলছি?",
        CODE: "আপনাকে নিশ্চিত করতে, আপনার পেটিএম অ্যাপে এখন একটা চার সংখ্যার কোড এসেছে। কোডটা বলুন।",
        ASK: "{salesman} {signed} তারিখে আপনাকে মাসে {price} টাকার প্ল্যান দিয়েছিলেন, {starts} থেকে। আপনি কি এই প্ল্যানটাই নিয়েছিলেন?",
        READ_BACK: "তাহলে {starts} থেকে প্রতি মাসে {price} টাকা। এটা পাকা করে দেব?",
        CHARGED: "ধন্যবাদ। আপনার প্ল্যান {starts} থেকে শুরু হবে, একটা এসএমএসও আসবে। ভালো থাকবেন।",
        FOLLOW_UP: "অসুবিধার জন্য দুঃখিত। এখন কিছু কাটা হবে না। পেটিএমের একজন সঠিক অফার নিয়ে আপনাকে ফোন করবেন, আর সব তথ্য হোয়াটসঅ্যাপে পাঠাচ্ছি। ধন্যবাদ।",
        GOODBYE_OTHER: "কোনো অসুবিধা নেই। {owner}-কে বলবেন পেটিএম থেকে ফোন এসেছিল, আমরা পরে কথা বলব। ধন্যবাদ।",
        GOODBYE_UNVERIFIED: "দুঃখিত, আমরা পরিচয় নিশ্চিত করতে পারিনি, তাই কিছু বদলায়নি। পেটিএমের একজন রেজিস্টার্ড নম্বরে ফোন করবেন। ধন্যবাদ।",
    },
    "gu": {
        "name": "Gujarati", "own": "ગુજરાતી", "code": "gu-IN", "voice": "ratan",
        "months": "જાન્યુઆરી ફેબ્રુઆરી માર્ચ એપ્રિલ મે જૂન જુલાઈ ઓગસ્ટ સપ્ટેમ્બર ઓક્ટોબર નવેમ્બર ડિસેમ્બર",
        CONSENT: "નમસ્તે, હું પેટીએમથી બોલું છું, તમારા સાઉન્ડબોક્સ વિશે. આ કોલ રેકોર્ડ થઈ રહ્યો છે, ચાલશે?",
        NAME_RECORDED: "આભાર. શું હું {owner} સાથે વાત કરી રહ્યો છું?",
        NAME_UNRECORDED: "બરાબર, આ કોલ રેકોર્ડ નહીં થાય. શું હું {owner} સાથે વાત કરી રહ્યો છું?",
        CODE: "તમારી ઓળખ માટે, તમારા પેટીએમ એપ પર હમણાં ચાર અંકનો કોડ આવ્યો છે. એ કોડ કહો.",
        ASK: "{salesman}એ {signed}ના રોજ તમને મહિને {price} રૂપિયાનો પ્લાન આપ્યો હતો, {starts}થી. શું તમે આ જ પ્લાન લીધો હતો?",
        READ_BACK: "તો {starts}થી દર મહિને {price} રૂપિયા. પાક્કું કરી દઉં?",
        CHARGED: "આભાર. તમારો પ્લાન {starts}થી શરૂ થશે, એસએમએસ પણ આવશે. તમારો દિવસ સારો જાય.",
        FOLLOW_UP: "તકલીફ બદલ માફ કરશો. હમણાં કંઈ કપાશે નહીં. પેટીએમની ટીમ સાચી ઓફર સાથે તમને ફોન કરશે, અને બધી માહિતી વોટ્સએપ પર મોકલીએ છીએ. આભાર.",
        GOODBYE_OTHER: "કોઈ વાંધો નહીં. {owner}ને કહેજો કે પેટીએમથી ફોન આવ્યો હતો, અમે પછી વાત કરીશું. આભાર.",
        GOODBYE_UNVERIFIED: "માફ કરશો, અમે ઓળખ પાક્કી ન કરી શક્યા, એટલે કંઈ બદલાયું નથી. પેટીએમની ટીમ રજિસ્ટર્ડ નંબર પર ફોન કરશે. આભાર.",
    },
    "kn": {
        "name": "Kannada", "own": "ಕನ್ನಡ", "code": "kn-IN", "voice": "shubh", "month_first": True,
        "months": "ಜನವರಿ ಫೆಬ್ರವರಿ ಮಾರ್ಚ್ ಏಪ್ರಿಲ್ ಮೇ ಜೂನ್ ಜುಲೈ ಆಗಸ್ಟ್ ಸೆಪ್ಟೆಂಬರ್ ಅಕ್ಟೋಬರ್ ನವೆಂಬರ್ ಡಿಸೆಂಬರ್",
        CONSENT: "ನಮಸ್ಕಾರ, ನಾನು ಪೇಟಿಎಂನಿಂದ ಮಾತಾಡ್ತಿದ್ದೀನಿ, ನಿಮ್ಮ ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಬಗ್ಗೆ. ಈ ಕರೆ ರೆಕಾರ್ಡ್ ಆಗ್ತಿದೆ, ಪರವಾಗಿಲ್ವಾ?",
        NAME_RECORDED: "ಧನ್ಯವಾದ. ನಾನು {owner} ಅವರ ಜೊತೆ ಮಾತಾಡ್ತಿದ್ದೀನಾ?",
        NAME_UNRECORDED: "ಸರಿ, ಈ ಕರೆ ರೆಕಾರ್ಡ್ ಆಗಲ್ಲ. ನಾನು {owner} ಅವರ ಜೊತೆ ಮಾತಾಡ್ತಿದ್ದೀನಾ?",
        CODE: "ನಿಮ್ಮ ಗುರುತು ಖಚಿತಪಡಿಸಲು, ನಿಮ್ಮ ಪೇಟಿಎಂ ಆ್ಯಪ್‌ಗೆ ಈಗ ನಾಲ್ಕು ಅಂಕಿಯ ಕೋಡ್ ಬಂದಿದೆ. ಆ ಕೋಡ್ ಹೇಳಿ.",
        ASK: "{salesman} {signed} ರಂದು ನಿಮಗೆ ತಿಂಗಳಿಗೆ {price} ರೂಪಾಯಿ ಪ್ಲಾನ್ ಕೊಟ್ಟಿದ್ರು, {starts} ರಿಂದ. ನೀವು ಇದೇ ಪ್ಲಾನ್ ತಗೊಂಡಿದ್ರಾ?",
        READ_BACK: "ಹಾಗಾದ್ರೆ {starts} ರಿಂದ ಪ್ರತಿ ತಿಂಗಳು {price} ರೂಪಾಯಿ. ಖಚಿತ ಮಾಡ್ಲಾ?",
        CHARGED: "ಧನ್ಯವಾದ. ನಿಮ್ಮ ಪ್ಲಾನ್ {starts} ರಿಂದ ಶುರು ಆಗುತ್ತೆ, ಎಸ್‌ಎಂಎಸ್ ಕೂಡ ಬರುತ್ತೆ. ಒಳ್ಳೆಯ ದಿನ.",
        FOLLOW_UP: "ತೊಂದರೆಗೆ ಕ್ಷಮಿಸಿ. ಈಗ ಏನೂ ಕಡಿತ ಆಗಲ್ಲ. ಪೇಟಿಎಂ ತಂಡ ಸರಿಯಾದ ಆಫರ್ ಜೊತೆ ನಿಮಗೆ ಕರೆ ಮಾಡುತ್ತೆ, ಎಲ್ಲಾ ವಿವರ ವಾಟ್ಸಾಪ್‌ಗೆ ಕಳಿಸ್ತಿದ್ದೀವಿ. ಧನ್ಯವಾದ.",
        GOODBYE_OTHER: "ಪರವಾಗಿಲ್ಲ. ಪೇಟಿಎಂನಿಂದ ಕರೆ ಬಂದಿತ್ತು ಅಂತ {owner} ಅವರಿಗೆ ಹೇಳಿ, ನಾವು ಆಮೇಲೆ ಮಾತಾಡ್ತೀವಿ. ಧನ್ಯವಾದ.",
        GOODBYE_UNVERIFIED: "ಕ್ಷಮಿಸಿ, ಗುರುತು ಖಚಿತ ಆಗಲಿಲ್ಲ, ಅದಕ್ಕೆ ಏನೂ ಬದಲಾಗಿಲ್ಲ. ಪೇಟಿಎಂ ತಂಡ ನೋಂದಾಯಿತ ನಂಬರ್‌ಗೆ ಕರೆ ಮಾಡುತ್ತೆ. ಧನ್ಯವಾದ.",
    },
    "ml": {
        "name": "Malayalam", "own": "മലയാളം", "code": "ml-IN", "voice": "shubh", "month_first": True,
        "months": "ജനുവരി ഫെബ്രുവരി മാർച്ച് ഏപ്രിൽ മേയ് ജൂൺ ജൂലൈ ഓഗസ്റ്റ് സെപ്റ്റംബർ ഒക്ടോബർ നവംബർ ഡിസംബർ",
        CONSENT: "നമസ്കാരം, ഞാൻ പേടിഎമ്മിൽ നിന്നാണ് വിളിക്കുന്നത്, നിങ്ങളുടെ സൗണ്ട്ബോക്സിനെ കുറിച്ച്. ഈ കോൾ റെക്കോർഡ് ചെയ്യുന്നുണ്ട്, കുഴപ്പമുണ്ടോ?",
        NAME_RECORDED: "നന്ദി. ഞാൻ {owner}-നോടാണോ സംസാരിക്കുന്നത്?",
        NAME_UNRECORDED: "ശരി, ഈ കോൾ റെക്കോർഡ് ചെയ്യില്ല. ഞാൻ {owner}-നോടാണോ സംസാരിക്കുന്നത്?",
        CODE: "നിങ്ങളാണെന്ന് ഉറപ്പാക്കാൻ, നിങ്ങളുടെ പേടിഎം ആപ്പിൽ ഇപ്പോൾ ഒരു നാലക്ക കോഡ് വന്നിട്ടുണ്ട്. ആ കോഡ് പറയൂ.",
        ASK: "{salesman} {signed}-ന് നിങ്ങൾക്ക് മാസം {price} രൂപയുടെ പ്ലാൻ തന്നിരുന്നു, {starts} മുതൽ. നിങ്ങൾ ഈ പ്ലാൻ തന്നെയാണോ എടുത്തത്?",
        READ_BACK: "അപ്പോൾ {starts} മുതൽ മാസം {price} രൂപ. ഉറപ്പിക്കട്ടെ?",
        CHARGED: "നന്ദി. നിങ്ങളുടെ പ്ലാൻ {starts} മുതൽ തുടങ്ങും, ഒരു എസ്എംഎസും വരും. നല്ല ദിവസം.",
        FOLLOW_UP: "ബുദ്ധിമുട്ടിന് ക്ഷമിക്കണം. ഇപ്പോൾ ഒന്നും പിടിക്കില്ല. പേടിഎം ടീം ശരിയായ ഓഫറുമായി നിങ്ങളെ വിളിക്കും, എല്ലാ വിവരങ്ങളും വാട്ട്സ്ആപ്പിൽ അയയ്ക്കുന്നു. നന്ദി.",
        GOODBYE_OTHER: "കുഴപ്പമില്ല. പേടിഎമ്മിൽ നിന്ന് വിളിച്ചിരുന്നു എന്ന് {owner}-നോട് പറയൂ, ഞങ്ങൾ പിന്നീട് സംസാരിക്കാം. നന്ദി.",
        GOODBYE_UNVERIFIED: "ക്ഷമിക്കണം, ആളെ ഉറപ്പാക്കാൻ കഴിഞ്ഞില്ല, അതുകൊണ്ട് ഒന്നും മാറിയിട്ടില്ല. പേടിഎം ടീം രജിസ്റ്റർ ചെയ്ത നമ്പറിൽ വിളിക്കും. നന്ദി.",
    },
    "mr": {
        "name": "Marathi", "own": "मराठी", "code": "mr-IN", "voice": "ratan",
        "months": "जानेवारी फेब्रुवारी मार्च एप्रिल मे जून जुलै ऑगस्ट सप्टेंबर ऑक्टोबर नोव्हेंबर डिसेंबर",
        CONSENT: "नमस्कार, मी पेटीएममधून बोलतोय, तुमच्या साउंडबॉक्सबद्दल. हा कॉल रेकॉर्ड होतोय, चालेल का?",
        NAME_RECORDED: "धन्यवाद. मी {owner} यांच्याशी बोलतोय का?",
        NAME_UNRECORDED: "ठीक आहे, हा कॉल रेकॉर्ड होणार नाही. मी {owner} यांच्याशी बोलतोय का?",
        CODE: "तुमची ओळख पक्की करण्यासाठी, तुमच्या पेटीएम ॲपवर आत्ता चार अंकी कोड आलाय. तो कोड सांगा.",
        ASK: "{salesman} यांनी {signed} ला तुम्हाला महिन्याला {price} रुपयांचा प्लॅन दिला होता, {starts} पासून. तुम्ही हाच प्लॅन घेतला होता का?",
        READ_BACK: "म्हणजे {starts} पासून दर महिन्याला {price} रुपये. पक्कं करू?",
        CHARGED: "धन्यवाद. तुमचा प्लॅन {starts} पासून सुरू होईल, एसएमएसही येईल. तुमचा दिवस चांगला जावो.",
        FOLLOW_UP: "त्रासाबद्दल माफ करा. आत्ता काहीही कापलं जाणार नाही. पेटीएमची टीम योग्य ऑफरसह तुम्हाला फोन करेल, आणि सगळी माहिती व्हॉट्सॲपवर पाठवतोय. धन्यवाद.",
        GOODBYE_OTHER: "काही हरकत नाही. {owner} यांना सांगा की पेटीएममधून फोन आला होता, आम्ही नंतर बोलू. धन्यवाद.",
        GOODBYE_UNVERIFIED: "माफ करा, ओळख पक्की झाली नाही, म्हणून काहीही बदललेलं नाही. पेटीएमची टीम नोंदणीकृत नंबरवर फोन करेल. धन्यवाद.",
    },
    "od": {
        "name": "Odia", "own": "ଓଡ଼ିଆ", "code": "od-IN", "voice": "shubh",
        "months": "ଜାନୁଆରୀ ଫେବୃଆରୀ ମାର୍ଚ୍ଚ ଅପ୍ରେଲ ମେ ଜୁନ ଜୁଲାଇ ଅଗଷ୍ଟ ସେପ୍ଟେମ୍ବର ଅକ୍ଟୋବର ନଭେମ୍ବର ଡିସେମ୍ବର",
        CONSENT: "ନମସ୍କାର, ମୁଁ ପେଟିଏମରୁ କହୁଛି, ଆପଣଙ୍କ ସାଉଣ୍ଡବକ୍ସ ବିଷୟରେ। ଏହି କଲ ରେକର୍ଡ ହେଉଛି, ଠିକ ଅଛି?",
        NAME_RECORDED: "ଧନ୍ୟବାଦ। ମୁଁ କଣ {owner}ଙ୍କ ସହ କଥା ହେଉଛି?",
        NAME_UNRECORDED: "ଠିକ ଅଛି, ଏହି କଲ ରେକର୍ଡ ହେବ ନାହିଁ। ମୁଁ କଣ {owner}ଙ୍କ ସହ କଥା ହେଉଛି?",
        CODE: "ଆପଣଙ୍କ ପରିଚୟ ପାଇଁ, ଆପଣଙ୍କ ପେଟିଏମ ଆପରେ ଏବେ ଚାରି ଅଙ୍କର କୋଡ ଆସିଛି। ସେହି କୋଡ କୁହନ୍ତୁ।",
        ASK: "{salesman} {signed}ରେ ଆପଣଙ୍କୁ ମାସକୁ {price} ଟଙ୍କାର ପ୍ଲାନ ଦେଇଥିଲେ, {starts}ରୁ। ଆପଣ କଣ ଏହି ପ୍ଲାନ ନେଇଥିଲେ?",
        READ_BACK: "ତେବେ {starts}ରୁ ପ୍ରତି ମାସ {price} ଟଙ୍କା। ପକ୍କା କରିଦେବି?",
        CHARGED: "ଧନ୍ୟବାଦ। ଆପଣଙ୍କ ପ୍ଲାନ {starts}ରୁ ଆରମ୍ଭ ହେବ, ଏସଏମଏସ ମଧ୍ୟ ଆସିବ। ଶୁଭ ଦିନ।",
        FOLLOW_UP: "ଅସୁବିଧା ପାଇଁ କ୍ଷମା କରନ୍ତୁ। ଏବେ କିଛି କଟିବ ନାହିଁ। ପେଟିଏମ ଟିମ ଠିକ ଅଫର ସହ ଆପଣଙ୍କୁ କଲ କରିବ, ଆଉ ସବୁ ତଥ୍ୟ ହ୍ୱାଟସଆପରେ ପଠାଉଛୁ। ଧନ୍ୟବାଦ।",
        GOODBYE_OTHER: "କିଛି ଅସୁବିଧା ନାହିଁ। {owner}ଙ୍କୁ କହିବେ ପେଟିଏମରୁ କଲ ଆସିଥିଲା, ଆମେ ପରେ କଥା ହେବୁ। ଧନ୍ୟବାଦ।",
        GOODBYE_UNVERIFIED: "କ୍ଷମା କରନ୍ତୁ, ପରିଚୟ ପକ୍କା ହେଲା ନାହିଁ, ତେଣୁ କିଛି ବଦଳିନାହିଁ। ପେଟିଏମ ଟିମ ରେଜିଷ୍ଟର୍ଡ ନମ୍ବରରେ କଲ କରିବ। ଧନ୍ୟବାଦ।",
    },
    "pa": {
        "name": "Punjabi", "own": "ਪੰਜਾਬੀ", "code": "pa-IN", "voice": "mani",
        "months": "ਜਨਵਰੀ ਫ਼ਰਵਰੀ ਮਾਰਚ ਅਪ੍ਰੈਲ ਮਈ ਜੂਨ ਜੁਲਾਈ ਅਗਸਤ ਸਤੰਬਰ ਅਕਤੂਬਰ ਨਵੰਬਰ ਦਸੰਬਰ",
        CONSENT: "ਸਤ ਸ੍ਰੀ ਅਕਾਲ ਜੀ, ਮੈਂ ਪੇਟੀਐਮ ਤੋਂ ਬੋਲ ਰਿਹਾ ਹਾਂ, ਤੁਹਾਡੇ ਸਾਊਂਡਬਾਕਸ ਬਾਰੇ। ਇਹ ਕਾਲ ਰਿਕਾਰਡ ਹੋ ਰਹੀ ਹੈ, ਠੀਕ ਹੈ?",
        NAME_RECORDED: "ਧੰਨਵਾਦ ਜੀ। ਕੀ ਮੈਂ {owner} ਜੀ ਨਾਲ ਗੱਲ ਕਰ ਰਿਹਾ ਹਾਂ?",
        NAME_UNRECORDED: "ਠੀਕ ਹੈ, ਇਹ ਕਾਲ ਰਿਕਾਰਡ ਨਹੀਂ ਹੋਵੇਗੀ। ਕੀ ਮੈਂ {owner} ਜੀ ਨਾਲ ਗੱਲ ਕਰ ਰਿਹਾ ਹਾਂ?",
        CODE: "ਪਛਾਣ ਪੱਕੀ ਕਰਨ ਲਈ, ਤੁਹਾਡੀ ਪੇਟੀਐਮ ਐਪ ਤੇ ਹੁਣੇ ਚਾਰ ਅੰਕਾਂ ਦਾ ਕੋਡ ਆਇਆ ਹੈ। ਉਹ ਕੋਡ ਦੱਸ ਦਿਓ।",
        ASK: "{salesman} ਨੇ {signed} ਨੂੰ ਤੁਹਾਨੂੰ ਮਹੀਨੇ ਦਾ {price} ਰੁਪਏ ਵਾਲਾ ਪਲਾਨ ਦਿੱਤਾ ਸੀ, {starts} ਤੋਂ। ਕੀ ਤੁਸੀਂ ਇਹੀ ਪਲਾਨ ਲਿਆ ਸੀ?",
        READ_BACK: "ਤਾਂ {starts} ਤੋਂ ਹਰ ਮਹੀਨੇ {price} ਰੁਪਏ। ਪੱਕਾ ਕਰ ਦਿਆਂ?",
        CHARGED: "ਬਹੁਤ ਧੰਨਵਾਦ। ਤੁਹਾਡਾ ਪਲਾਨ {starts} ਤੋਂ ਸ਼ੁਰੂ ਹੋਵੇਗਾ, ਐਸਐਮਐਸ ਵੀ ਆ ਜਾਵੇਗਾ। ਤੁਹਾਡਾ ਦਿਨ ਵਧੀਆ ਲੰਘੇ।",
        FOLLOW_UP: "ਤਕਲੀਫ਼ ਲਈ ਮਾਫ਼ ਕਰਨਾ। ਹੁਣ ਕੁਝ ਨਹੀਂ ਕੱਟੇਗਾ। ਪੇਟੀਐਮ ਦੀ ਟੀਮ ਸਹੀ ਆਫ਼ਰ ਨਾਲ ਤੁਹਾਨੂੰ ਕਾਲ ਕਰੇਗੀ, ਤੇ ਸਾਰੀ ਜਾਣਕਾਰੀ ਵਟਸਐਪ ਤੇ ਭੇਜ ਰਹੇ ਹਾਂ। ਧੰਨਵਾਦ।",
        GOODBYE_OTHER: "ਕੋਈ ਗੱਲ ਨਹੀਂ। {owner} ਜੀ ਨੂੰ ਦੱਸ ਦਿਓ ਕਿ ਪੇਟੀਐਮ ਤੋਂ ਕਾਲ ਆਈ ਸੀ, ਅਸੀਂ ਬਾਅਦ ਵਿੱਚ ਗੱਲ ਕਰ ਲਵਾਂਗੇ। ਧੰਨਵਾਦ।",
        GOODBYE_UNVERIFIED: "ਮਾਫ਼ ਕਰਨਾ, ਅਸੀਂ ਪਛਾਣ ਪੱਕੀ ਨਹੀਂ ਕਰ ਸਕੇ, ਇਸ ਲਈ ਕੁਝ ਨਹੀਂ ਬਦਲਿਆ। ਪੇਟੀਐਮ ਦੀ ਟੀਮ ਰਜਿਸਟਰਡ ਨੰਬਰ ਤੇ ਕਾਲ ਕਰੇਗੀ। ਧੰਨਵਾਦ।",
    },
    "ta": {
        "name": "Tamil", "own": "தமிழ்", "code": "ta-IN", "voice": "ratan", "month_first": True,
        "months": "ஜனவரி பிப்ரவரி மார்ச் ஏப்ரல் மே ஜூன் ஜூலை ஆகஸ்ட் செப்டம்பர் அக்டோபர் நவம்பர் டிசம்பர்",
        CONSENT: "வணக்கம், நான் பேடிஎம்-லிருந்து பேசுகிறேன், உங்கள் சவுண்ட்பாக்ஸ் பற்றி. இந்த அழைப்பு பதிவு செய்யப்படுகிறது, பரவாயில்லையா?",
        NAME_RECORDED: "நன்றி. நான் {owner} அவர்களிடம் பேசுகிறேனா?",
        NAME_UNRECORDED: "சரி, இந்த அழைப்பு பதிவு செய்யப்படாது. நான் {owner} அவர்களிடம் பேசுகிறேனா?",
        CODE: "நீங்கள்தான் என்று உறுதி செய்ய, உங்கள் பேடிஎம் ஆப்பில் இப்போது நான்கு இலக்க குறியீடு வந்துள்ளது. அதைச் சொல்லுங்கள்.",
        ASK: "{salesman} {signed} அன்று உங்களுக்கு மாதம் {price} ரூபாய் பிளானைக் கொடுத்தார், {starts} முதல். இந்த பிளானைத்தான் எடுத்தீர்களா?",
        READ_BACK: "அப்போ {starts} முதல் மாதம் {price} ரூபாய். உறுதி செய்யட்டுமா?",
        CHARGED: "நன்றி. உங்கள் பிளான் {starts} முதல் தொடங்கும், ஒரு எஸ்எம்எஸ்-ம் வரும். நல்ல நாள்.",
        FOLLOW_UP: "சிரமத்திற்கு மன்னிக்கவும். இப்போது எதுவும் எடுக்கப்படாது. பேடிஎம் குழு சரியான ஆஃபருடன் உங்களை அழைக்கும், எல்லா விவரங்களையும் வாட்ஸ்அப்பில் அனுப்புகிறோம். நன்றி.",
        GOODBYE_OTHER: "பரவாயில்லை. பேடிஎம்-லிருந்து அழைத்தோம் என்று {owner} அவர்களிடம் சொல்லுங்கள், பிறகு பேசுகிறோம். நன்றி.",
        GOODBYE_UNVERIFIED: "மன்னிக்கவும், அடையாளத்தை உறுதி செய்ய முடியவில்லை, அதனால் எதுவும் மாறவில்லை. பேடிஎம் குழு பதிவு செய்த எண்ணில் அழைக்கும். நன்றி.",
    },
    "te": {
        "name": "Telugu", "own": "తెలుగు", "code": "te-IN", "voice": "shubh", "month_first": True,
        "months": "జనవరి ఫిబ్రవరి మార్చి ఏప్రిల్ మే జూన్ జూలై ఆగస్టు సెప్టెంబర్ అక్టోబర్ నవంబర్ డిసెంబర్",
        CONSENT: "నమస్తే, నేను పేటీఎం నుండి మాట్లాడుతున్నాను, మీ సౌండ్‌బాక్స్ గురించి. ఈ కాల్ రికార్డ్ అవుతోంది, పర్వాలేదా?",
        NAME_RECORDED: "ధన్యవాదాలు. నేను {owner} గారితో మాట్లాడుతున్నానా?",
        NAME_UNRECORDED: "సరే, ఈ కాల్ రికార్డ్ అవ్వదు. నేను {owner} గారితో మాట్లాడుతున్నానా?",
        CODE: "మీరేనని నిర్ధారించడానికి, మీ పేటీఎం యాప్‌కి ఇప్పుడే నాలుగు అంకెల కోడ్ వచ్చింది. ఆ కోడ్ చెప్పండి.",
        ASK: "{salesman} {signed} న మీకు నెలకు {price} రూపాయల ప్లాన్ ఇచ్చారు, {starts} నుండి. మీరు ఇదే ప్లాన్ తీసుకున్నారా?",
        READ_BACK: "అంటే {starts} నుండి ప్రతి నెల {price} రూపాయలు. ఖరారు చేయనా?",
        CHARGED: "ధన్యవాదాలు. మీ ప్లాన్ {starts} నుండి మొదలవుతుంది, ఎస్ఎంఎస్ కూడా వస్తుంది. మంచి రోజు.",
        FOLLOW_UP: "ఇబ్బందికి క్షమించండి. ఇప్పుడు ఏమీ కట్ కాదు. పేటీఎం టీమ్ సరైన ఆఫర్‌తో మీకు కాల్ చేస్తుంది, పూర్తి వివరాలు వాట్సాప్‌లో పంపుతున్నాం. ధన్యవాదాలు.",
        GOODBYE_OTHER: "పర్వాలేదు. పేటీఎం నుండి కాల్ వచ్చిందని {owner} గారికి చెప్పండి, మేము తర్వాత మాట్లాడతాం. ధన్యవాదాలు.",
        GOODBYE_UNVERIFIED: "క్షమించండి, గుర్తింపు నిర్ధారించలేకపోయాం, అందుకే ఏమీ మారలేదు. పేటీఎం టీమ్ రిజిస్టర్డ్ నంబర్‌కి కాల్ చేస్తుంది. ధన్యవాదాలు.",
    },
    "en": {
        "name": "English", "own": "English", "code": "en-IN", "voice": "ratan",
        "months": "January February March April May June July August September October November December",
        **{key: key for key in LINES},
    },
}


def _date(language, iso):
    d = date.fromisoformat(iso)
    month = LANGUAGES[language]["months"].split()[d.month - 1]
    return f"{month} {d.day}" if LANGUAGES[language].get("month_first") else f"{d.day} {month}"


def fields(language, shop):
    """The record's facts as this language says them."""
    s = shop.signup or {}
    man = s.get("salesman") or {}
    return {
        "owner": shop.say.get(language) or shop.owner or shop.name,
        "salesman": man.get("say", {}).get(language) or man.get("name", "").split(" ")[0] or "our salesman",
        "price": s.get("price", ""),
        "signed": _date(language, s["on"]) if s.get("on") else "",
        "starts": _date(language, s["starts"]) if s.get("starts") else "",
    }


def say(language, line, shop):
    """The line as spoken in language, filled from the shop's record."""
    return LANGUAGES[language][line].format(**fields(language, shop))


def english(line, shop):
    return say("en", line, shop)
