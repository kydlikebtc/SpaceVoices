import nltk

def download_data():
    """Download required NLTK data for TextBlob."""
    nltk.download('punkt')

if __name__ == '__main__':
    download_data()
