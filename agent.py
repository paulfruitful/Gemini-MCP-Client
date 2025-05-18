from google import genai
import re
import json
      
class Agent:
    def __init__(self, model,tools,key):
        self.model = model
        self.tools=tools
        self.history = []
        self.key=key


    def find_tool(self, tool_name):
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None
        

    def process_query(self, query):
        prompt = f"""
        QUERY: {query}
        
        AVAILABLE TOOLS: {', '.join( [{
        "name": tool.name,
        "description": tool.description
    } for tool in response.tools])}
        
        INSTRUCTIONS:
        1. Analyze if the query requires using any of the available tools.
        2. Respond in the following JSON format:
           {{"needs_tool": true/false, "tool_name": "tool_name_if_needed", "reasoning": "brief explanation"}}
        3. If no tool is needed, set "needs_tool" to false and leave "tool_name" empty.
        
        Your structured response:
        """
        
        response = self.generate_response(prompt)
        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": response})
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

    def process_use_tool(self, tool_name):
        tool = self.find_tool(tool_name)
        if tool:
            prompt = f"""
            # Tool Calling Task
            
            ## Context
            You are analyzing a conversation to extract parameters for a tool call.
            
            ## Tool Information
            - Name: {tool.name}
            - Description: {tool.description}
            - Input Schema: {tool.input_schema}
            
            ## Previous Conversation
            User query: {self.history[-2]['content']}
            Assistant response: {self.history[-1]['content']}
            
            ## Instructions
            1. Carefully analyze the conversation above
            2. Extract all necessary parameters required by the tool's input schema
            3. Format values appropriately according to their expected types
            4. Do not add any parameters not specified in the schema
            5. If a required parameter is missing from the conversation, use a reasonable default or placeholder
            
            ## Response Format
            Respond ONLY with a valid JSON object in this exact format:
            {{
                "tool_name": "{tool.name}",
                "input": {{
                    "parameter1": "value1",
                    "parameter2": "value2",
                    ... 
                }}
            }}
            """
            
            response = self.generate_response(prompt)
            parsed_response = self.extract_json(response)
            
            return parsed_response
        else:
            return {"error": f"Tool '{tool_name}' not found"}

    def generate_response(self, prompt):
        response = genai.generate_text(
            model=self.model,
            prompt=prompt,
            temperature=0.7,
            max_output_tokens=100,
        )
        return response.text
