from dotenv import load_dotenv
from openai import AzureOpenAI
import os


def get_questions(theme: str = None) -> list[dict]:
    """
    Generate questions and answers based on a specified theme

    Args:
        theme (str, optional): Theme for the questions. Defaults to None.

    Returns:
        list[dict]: A list of 3 question dictionaries, each containing:
            - question (str): The question
            - answer (list[str]): List of the 6 answers
            - points (list[int]): Corresponding points for each answer
    """
    load_dotenv()
    AZURE_API_KEY = os.getenv("AZURE_API_KEY")

    # Initialize the client
    client = AzureOpenAI(
        azure_endpoint="https://cuhk-apip.azure-api.net",
        api_version="2024-06-01",
        api_key=AZURE_API_KEY,
    )

    theme_prompt = ""
    if theme != None:
        theme_prompt = "related to the theme " + theme

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": (
                    "Create 3 questions for playing the 'Guess Their Answer' game "
                    + theme_prompt
                    + ","
                    "each question has 10 answers with the first 6 answers being the most popular ones. "
                    "Do not use any text formatting in your response."
                    "Use 'Question 1: ','Question 2: ','Question 3: ' to indicate each question, "
                    "then use a numbered list for the answers"
                    "Assign a total of 100 points to the first 6 answers, put them in a bracket after each answer"
                ),
            },
        ],
        temperature=0.9,
    )
    res = response.choices[0].message.content
    # print(res)
    res = res.split("\n")

    ret = list()
    temp = dict()  # store current question
    for line in res:
        if line.find("Question") != -1:
            temp = dict()  # start a new question
            text = line[12:]
            temp["question"] = text
        else:
            answer = ""
            points = 0
            text = line.split()
            for word in text:
                if word.isalpha():
                    if answer != "":
                        answer += " "
                    answer += word
                elif word[0] == "(":
                    points = int(word[1:-1])
            if not "answer" in temp:
                temp["answer"] = list()
                temp["points"] = list()
            if len(temp["answer"]) == 5:
                temp["answer"].append(answer)
                temp["points"].append(points)
                ret.append(temp)
            elif len(temp["answer"]) < 5:
                temp["answer"].append(answer)
                temp["points"].append(points)
    return ret


if __name__ == "__main__":
    print(get_questions(theme="science"))
    print(get_questions(theme="internet"))
