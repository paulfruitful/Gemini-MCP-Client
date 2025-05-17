from google import genai
import re
import json
      
class Agent:
    def __init__(self, model,tools):
        self.model = model
        self.tools=tools
        self.history = []
        

    def process_query(self, query):
        prompt = f"""
        QUERY: {query}
        
        AVAILABLE TOOLS: {', '.join([tool['name']  for tool in self.tools])}
        
        INSTRUCTIONS:
        1. Analyze if the query requires using any of the available tools.
        2. Respond in the following JSON format:
           {{"needs_tool": true/false, "tool_name": "tool_name_if_needed", "reasoning": "brief explanation"}}
        3. If no tool is needed, set "needs_tool" to false and leave "tool_name" empty.
        
        Your structured response:
        """
        
        response = self.generate_response(prompt)
        parsedResponse = self.extract_json(response)
        
        return parsedResponse
        
    def extract_json(self, text):
        """Extract JSON content from text using regex."""
        
      
        try:
            match = re.search(r'{.*}', text, re.DOTALL)
            if match:
                json_str = match.group(0)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse JSON", "raw_text": json_str}
            else:
                return {"error": "No JSON found in response", "raw_text": text}
        except Exception as e:
            return {"error": str(e), "raw_text": text}

    def process_use_tool():
        #Would take tool name and description fetch the input schema and generate input
        return 



    def generate_response(self, prompt):
        response = genai.generate_text(
            model=self.model,
            prompt=prompt,
            temperature=0.7,
            max_output_tokens=100,
        )
        return response.text
