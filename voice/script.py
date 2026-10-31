# The three lines Settled says, keyed by language. Each constant is the English
# gloss the board shows and the key flow.py passes to the listener; LANGUAGES
# holds what is spoken, in each language's own script.
#
# Hindi is the hand-written line. Every other language is machine-written and
# needs a native speaker to check it before it goes in front of a real shop.
#
# The set is every language both Sarvam text-to-speech (bulbul:v3) and
# speech-to-text take, voices from docs.sarvam.ai bulbul-v3 best practices
# (2026-10-31).

ASK = "₹125 a month for the Soundbox from 1 Nov. Did you take this plan? Haan or na?"
READ_BACK = "₹125 every month, from 1 Nov. Sure?"
NA_FOLLOW_UP = "Okay, nothing is taken now. Shall I explain the real plans, or take the box back?"

LANGUAGES = {
    "hi": {
        "name": "Hindi", "own": "हिन्दी", "code": "hi-IN", "voice": "shubh",
        ASK: "1 नवंबर से साउंडबॉक्स का 125 रुपये महीना लगेगा. आपने यह प्लान लिया था? हाँ या ना?",
        READ_BACK: "125 रुपये हर महीने, 1 नवंबर से. पक्का?",
        NA_FOLLOW_UP: "ठीक है, अभी कुछ नहीं कटेगा. मैं असली प्लान समझाऊँ, या बॉक्स वापस ले जाएँ?",
    },
    "bn": {
        "name": "Bengali", "own": "বাংলা", "code": "bn-IN", "voice": "rehan",
        ASK: "1 নভেম্বর থেকে সাউন্ডবক্সের জন্য মাসে 125 টাকা লাগবে। আপনি কি এই প্ল্যানটা নিয়েছিলেন? হ্যাঁ নাকি না?",
        READ_BACK: "প্রতি মাসে 125 টাকা, 1 নভেম্বর থেকে। ঠিক তো?",
        NA_FOLLOW_UP: "ঠিক আছে, এখন কিছু কাটা হবে না। আসল প্ল্যানগুলো বুঝিয়ে বলব, নাকি বক্সটা ফেরত নিয়ে যাব?",
    },
    "gu": {
        "name": "Gujarati", "own": "ગુજરાતી", "code": "gu-IN", "voice": "ratan",
        ASK: "1 નવેમ્બરથી સાઉન્ડબોક્સના મહિને 125 રૂપિયા લાગશે. તમે આ પ્લાન લીધો હતો? હા કે ના?",
        READ_BACK: "દર મહિને 125 રૂપિયા, 1 નવેમ્બરથી. પાક્કું?",
        NA_FOLLOW_UP: "બરાબર, હમણાં કંઈ કપાશે નહીં. હું સાચા પ્લાન સમજાવું, કે બોક્સ પાછું લઈ જાઉં?",
    },
    "kn": {
        "name": "Kannada", "own": "ಕನ್ನಡ", "code": "kn-IN", "voice": "shubh",
        ASK: "ನವೆಂಬರ್ 1 ರಿಂದ ಸೌಂಡ್‌ಬಾಕ್ಸ್‌ಗೆ ತಿಂಗಳಿಗೆ 125 ರೂಪಾಯಿ. ನೀವು ಈ ಪ್ಲಾನ್ ತೆಗೆದುಕೊಂಡಿದ್ದೀರಾ? ಹೌದು ಅಥವಾ ಇಲ್ಲ?",
        READ_BACK: "ಪ್ರತಿ ತಿಂಗಳು 125 ರೂಪಾಯಿ, ನವೆಂಬರ್ 1 ರಿಂದ. ಖಚಿತವಾ?",
        NA_FOLLOW_UP: "ಸರಿ, ಈಗ ಏನೂ ಕಡಿತವಾಗುವುದಿಲ್ಲ. ನಿಜವಾದ ಪ್ಲಾನ್‌ಗಳನ್ನು ವಿವರಿಸಲಾ, ಅಥವಾ ಬಾಕ್ಸ್ ವಾಪಸ್ ತೆಗೆದುಕೊಂಡು ಹೋಗಲಾ?",
    },
    "ml": {
        "name": "Malayalam", "own": "മലയാളം", "code": "ml-IN", "voice": "shubh",
        ASK: "നവംബർ 1 മുതൽ സൗണ്ട്ബോക്സിന് മാസം 125 രൂപ. നിങ്ങൾ ഈ പ്ലാൻ എടുത്തിരുന്നോ? അതെ അല്ലെങ്കിൽ ഇല്ല?",
        READ_BACK: "മാസം 125 രൂപ, നവംബർ 1 മുതൽ. ഉറപ്പാണോ?",
        NA_FOLLOW_UP: "ശരി, ഇപ്പോൾ ഒന്നും പിടിക്കില്ല. ശരിയായ പ്ലാനുകൾ വിശദീകരിക്കട്ടെ, അതോ ബോക്സ് തിരികെ കൊണ്ടുപോകട്ടെ?",
    },
    "mr": {
        "name": "Marathi", "own": "मराठी", "code": "mr-IN", "voice": "ratan",
        ASK: "1 नोव्हेंबरपासून साउंडबॉक्सचे महिन्याला 125 रुपये लागतील. तुम्ही हा प्लॅन घेतला होता का? हो की नाही?",
        READ_BACK: "दर महिन्याला 125 रुपये, 1 नोव्हेंबरपासून. नक्की?",
        NA_FOLLOW_UP: "ठीक आहे, आत्ता काहीही कापले जाणार नाही. खरे प्लॅन समजावून सांगू, की बॉक्स परत घेऊन जाऊ?",
    },
    "od": {
        "name": "Odia", "own": "ଓଡ଼ିଆ", "code": "od-IN", "voice": "shubh",
        ASK: "1 ନଭେମ୍ବରରୁ ସାଉଣ୍ଡବକ୍ସ ପାଇଁ ମାସକୁ 125 ଟଙ୍କା ଲାଗିବ। ଆପଣ ଏହି ପ୍ଲାନ ନେଇଥିଲେ କି? ହଁ ନା ନାହିଁ?",
        READ_BACK: "ପ୍ରତି ମାସ 125 ଟଙ୍କା, 1 ନଭେମ୍ବରରୁ। ନିଶ୍ଚିତ?",
        NA_FOLLOW_UP: "ଠିକ ଅଛି, ଏବେ କିଛି କଟିବ ନାହିଁ। ପ୍ରକୃତ ପ୍ଲାନ ବୁଝାଇବି, ନା ବକ୍ସ ଫେରାଇ ନେଇଯିବି?",
    },
    "pa": {
        "name": "Punjabi", "own": "ਪੰਜਾਬੀ", "code": "pa-IN", "voice": "mani",
        ASK: "1 ਨਵੰਬਰ ਤੋਂ ਸਾਊਂਡਬਾਕਸ ਦਾ ਮਹੀਨੇ ਦਾ 125 ਰੁਪਏ ਲੱਗੇਗਾ। ਤੁਸੀਂ ਇਹ ਪਲਾਨ ਲਿਆ ਸੀ? ਹਾਂ ਜਾਂ ਨਾ?",
        READ_BACK: "ਹਰ ਮਹੀਨੇ 125 ਰੁਪਏ, 1 ਨਵੰਬਰ ਤੋਂ। ਪੱਕਾ?",
        NA_FOLLOW_UP: "ਠੀਕ ਹੈ, ਹੁਣ ਕੁਝ ਨਹੀਂ ਕੱਟੇਗਾ। ਮੈਂ ਅਸਲੀ ਪਲਾਨ ਸਮਝਾਵਾਂ, ਜਾਂ ਬਾਕਸ ਵਾਪਸ ਲੈ ਜਾਵਾਂ?",
    },
    "ta": {
        "name": "Tamil", "own": "தமிழ்", "code": "ta-IN", "voice": "ratan",
        ASK: "நவம்பர் 1 முதல் சவுண்ட்பாக்ஸுக்கு மாதம் 125 ரூபாய். இந்த பிளானை நீங்கள் எடுத்தீர்களா? ஆமாம் அல்லது இல்லை?",
        READ_BACK: "மாதம் 125 ரூபாய், நவம்பர் 1 முதல். உறுதியா?",
        NA_FOLLOW_UP: "சரி, இப்போது எதுவும் எடுக்கப்படாது. உண்மையான பிளான்களை சொல்லட்டுமா, அல்லது பாக்ஸை திரும்ப எடுக்கட்டுமா?",
    },
    "te": {
        "name": "Telugu", "own": "తెలుగు", "code": "te-IN", "voice": "shubh",
        ASK: "నవంబర్ 1 నుండి సౌండ్‌బాక్స్‌కు నెలకు 125 రూపాయలు. మీరు ఈ ప్లాన్ తీసుకున్నారా? అవును లేదా కాదు?",
        READ_BACK: "ప్రతి నెల 125 రూపాయలు, నవంబర్ 1 నుండి. ఖచ్చితమేనా?",
        NA_FOLLOW_UP: "సరే, ఇప్పుడు ఏమీ కట్ కాదు. అసలు ప్లాన్‌లు వివరించనా, లేదా బాక్స్ తిరిగి తీసుకెళ్ళనా?",
    },
    "en": {
        "name": "English", "own": "English", "code": "en-IN", "voice": "ratan",
        ASK: "From 1 November, the Soundbox costs 125 rupees a month. Did you take this plan? Yes or no?",
        READ_BACK: "125 rupees every month, from 1 November. Sure?",
        NA_FOLLOW_UP: "Okay, nothing is taken now. Shall I explain the real plans, or take the box back?",
    },
}


def line(language, said):
    return LANGUAGES[language][said]
