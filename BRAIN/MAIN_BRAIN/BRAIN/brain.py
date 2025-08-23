from FUNCTION.JARVIS_SPEAK.speak import *
from BRAIN.MAIN_BRAIN.GOOGLE_BIG_DATA.google_big_data import *
from BRAIN.MAIN_BRAIN.GOOGLE_SMALL_DATA.google_small_data import *
def load_qa_data(file_path):
    qa_dict = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(':')
                if len(parts) != 2:
                    continue
                q, a = parts
                qa_dict[q] = a
    return qa_dict

qa_file_path = r"C:\Users\Deepak Bairagi\Desktop\JARVIS 1.1\DATA\BRAIN_DATA\QNA_DATA\qna.txt" #give the correct path to your qa_data.txt file
qa_dict = load_qa_data(qa_file_path)

def brain_cmd(text):
    if "jarvis" in text:
        text = text.replace("jarvis", "")
        text = text.strip()
        if text in qa_dict:
            ans = qa_dict[text]
            return ans
        elif "define" in text:
            ans = deep_search(text)
            return ans
        else:
            ans = search_brain(text)
            return ans
    else:
        return "I didn't hear Jarvis in your command."
