from deep_translator import GoogleTranslator

class Translator:

    def translate(self, text):

        return GoogleTranslator(
            source='auto',
            target='vi'
        ).translate(text)