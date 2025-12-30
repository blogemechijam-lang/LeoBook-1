import ollama

class SemanticMatcher:
    def __init__(self, model='qwen3-vl:2b'):
        self.model = model

    def is_match(self, team1, team2, league=None):
        """
        Determines if two team names refer to the same entity.
        """
        context = ""
        if league:
            context = f"They play in the league: {league}."
            
        prompt = (
            f"Are the sports teams '{team1}' and '{team2}' the same team? "
            f"{context} "
            "Answer with exactly one word: 'Yes' or 'No'."
        )
        
        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt},
            ])
            ans = response['message']['content'].strip().lower()
            return 'yes' in ans
            
        except Exception as e:
            print(f"  [LLM Error] Failed to match {team1} vs {team2}: {e}")
            return False
