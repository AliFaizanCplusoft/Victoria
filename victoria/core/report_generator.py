"""
Report Generator - Generates comprehensive HTML reports with LLM content
"""

import os
import json
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Generates comprehensive HTML reports with LLM-generated content
    """
    
    def __init__(self, openai_client=None, template_path: str = "templates/html/vertria_comprehensive_report.html"):
        """Initialize report generator"""
        self.openai_client = openai_client
        self.template_path = template_path
        
        # Trait name mapping for display
        self.trait_name_mapping = {
            'A': 'Accountability', 'AD': 'Adaptability', 'C': 'Conflict Resolution',
            'CT': 'Critical Thinking', 'DA': 'Drive and Ambition', 'DM': 'Decision-Making',
            'EI': 'Emotional Intelligence', 'F': 'Approach to Failure', 'IN': 'Social Orientation',
            'IO': 'Innovation Orientation', 'N': 'Negotiation', 'PS': 'Problem-Solving',
            'RB': 'Relationship-Building', 'RG': 'Resilience and Grit', 'RT': 'Risk-Taking',
            'SL': 'Servant Leadership', 'TB': 'Team Building'
        }
    
    def generate_inspiring_content(self, profile_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate inspiring content using LLM"""
        try:
            if not self.openai_client:
                return self._generate_fallback_content(profile_data)
            
            # Generate executive summary
            executive_summary = self._generate_llm_content(
                'executive_summary',
                person_name=profile_data.get('person_name', 'You'),
                archetype_name=profile_data.get('archetype_name', 'Resilient Leadership'),
                overall_score=profile_data.get('overall_score', 85)
            )
            
            # Generate archetype description
            archetype_description = self._generate_llm_content(
                'archetype_description',
                person_name=profile_data.get('person_name', 'You'),
                archetype_name=profile_data.get('archetype_name', 'Resilient Leadership')
            )
            
            return {
                'executive_summary': executive_summary,
                'archetype_description': archetype_description
            }
            
        except Exception as e:
            logger.error(f"Error generating inspiring content: {e}")
            return self._generate_fallback_content(profile_data)
    
    def _generate_llm_content(self, content_type: str, **kwargs) -> str:
        """Generate LLM content for specific sections"""
        try:
            if not self.openai_client:
                return f"Generated content for {content_type}"
            
            # Extract open-ended responses for context
            open_ended_responses = kwargs.get('open_ended_responses', {})
            context = self._create_llm_context(kwargs, open_ended_responses)
            
            # Enhanced prompts with actual responses
            person_name = kwargs.get('person_name', 'a person')
            raw_archetype_name = kwargs.get('archetype_name', 'Resilient Leader')
            archetype_name = raw_archetype_name.replace('\\', '')
            
            prompts = {
                'executive_summary': f"""Write a personal, engaging executive summary for {person_name} who has been identified as a {archetype_name}.

Context from their responses:
{context}

Focus on their personal journey, their vision, and what makes them unique. Use their actual words and make it feel personal and inspiring. Avoid specific numbers or percentages.""",
                
                'archetype_description': f"""Write a personal description of what the {archetype_name} archetype means for this specific person.

Context from their responses:
{context}

Focus on how this archetype connects to their personal responses and journey. Make it feel personal and relevant to their specific situation. Avoid generic trait lists.""",
                
                'personalized_insights': f"""Provide personalized insights for {person_name} based on their {archetype_name} archetype and their specific responses.

Context from their responses:
{context}

Use their actual words and experiences to create relevant, personalized insights.""",
                
                'growth_opportunities_description': f"""Describe specific growth opportunities for {person_name} based on their {archetype_name} archetype and their responses.

Context from their responses:
{context}

Make the recommendations specific to their situation and goals.""",
                
                'next_steps_description': f"""Suggest concrete next steps for {person_name} based on their {archetype_name} archetype and their entrepreneurial journey.

Context from their responses:
{context}

Provide actionable, specific recommendations that align with their goals and current situation."""
            }
            
            prompt = prompts.get(content_type, f"Generate content for {content_type}")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating LLM content for {content_type}: {e}")
            return f"Generated content for {content_type}"
    
    def _generate_fallback_content(self, profile_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate fallback content when LLM is not available"""
        # Extract open-ended responses for personalized content
        open_ended_responses = profile_data.get('open_ended_responses', {})
        
        # Create personalized executive summary using actual responses
        executive_summary = self._create_personalized_executive_summary(profile_data, open_ended_responses)
        archetype_description = self._create_archetype_description(profile_data)
        
        return {
            'executive_summary': executive_summary,
            'archetype_description': archetype_description
        }
    
    
    
    def _create_llm_context(self, profile_data: Dict[str, Any], open_ended_responses: Dict[str, str]) -> str:
        """Create context for LLM from open-ended responses"""
        context_parts = []
        
        # Add key responses
        key_questions = [
            'Which of the following best describes where you are in your entrepreneurial journey?',
            'What does "entrepreneurship" mean to you personally?',
            'What kind of work energizes you most—and why?',
            'When you imagine your future, what role (if any) does building something yourself play?',
            'What are you learning about yourself right now—and what are you still figuring out?',
            'What inspired you to take this assessment today?',
            "What's a time when you took initiative or built something from scratch",
            'What fears or uncertainties do you have about starting something of your own?',
            'What kinds of work or challenges bring out the best in you?',
            'When have you taken the lead without being asked—and what happened?',
            'Where do you feel most confident in how you contribute?',
            "What's something others often rely on you for?",
            'How do you typically approach uncertainty or change?',
            'If you were to fully embrace your entrepreneurial energy, what might become possible?'
        ]
        
        for question in key_questions:
            if question in open_ended_responses and open_ended_responses[question]:
                context_parts.append(f"Q: {question}\nA: {open_ended_responses[question]}")
        
        return "\n\n".join(context_parts)
    
    def _load_trait_descriptions(self):
        """Load detailed trait descriptions from trait.txt file"""
        # Get the project root directory (where victoria_pipeline.py is located)
        # From victoria/core/report_generator.py -> victoria/core -> victoria -> project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        trait_file_path = os.path.join(project_root, 'trait.txt')
        logger.info(f"Looking for trait.txt at: {trait_file_path}")
        logger.info(f"File exists: {os.path.exists(trait_file_path)}")
        try:
            with open(trait_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the trait descriptions from the file
            trait_descriptions = {}
            sections = content.split('Trait ')
            
            for section in sections[1:]:  # Skip first empty section
                lines = section.strip().split('\n')
                if len(lines) < 2:
                    continue
                    
                # Extract trait name and code
                trait_line = lines[0]
                if ':' in trait_line:
                    trait_name = trait_line.split(':')[1].strip()
                    trait_code = self._get_trait_code_from_name(trait_name)
                    
                    # Extract strength and growth area descriptions
                    # Special handling for IN trait which has two "as a Strength" sections
                    strength_text = ""
                    growth_text = ""
                    extroversion_text = ""
                    introversion_text = ""
                    
                    current_section = ""
                    for line in lines[1:]:
                        if "Extroversion as a Strength" in line:
                            current_section = "extroversion"
                        elif "Introversion as a Strength" in line:
                            current_section = "introversion"
                        elif "as a Strength" in line and trait_code != 'IN':
                            current_section = "strength"
                        elif "as a Growth Area" in line:
                            current_section = "growth"
                        elif line.strip() and current_section:
                            if current_section == "strength":
                                strength_text += line.strip() + " "
                            elif current_section == "growth":
                                growth_text += line.strip() + " "
                            elif current_section == "extroversion":
                                extroversion_text += line.strip() + " "
                            elif current_section == "introversion":
                                introversion_text += line.strip() + " "
                    
                    if trait_code:
                        # Special handling for IN trait (Social Orientation)
                        if trait_code == 'IN':
                            trait_descriptions[trait_code] = {
                                'high_extro': extroversion_text.strip(),
                                'high_intro': introversion_text.strip(),
                                'low': growth_text.strip()
                            }
                        else:
                            trait_descriptions[trait_code] = {
                                'high': strength_text.strip(),
                                'low': growth_text.strip()
                            }
            
            return trait_descriptions
        except Exception as e:
            logger.error(f"Error loading trait descriptions: {e}")
            return {}
    
    def _get_trait_code_from_name(self, trait_name: str) -> str:
        """Map trait name to trait code"""
        name_to_code = {
            'Risk-Taking': 'RT',
            'Introversion and Extroversion': 'IN',  # Keep for backward compatibility with trait.txt
            'Social Orientation': 'IN',  # New name
            'Relationship-Building': 'RB',
            'Decision-Making': 'DM',
            'Problem-Solving': 'PS',
            'Critical Thinking': 'CT',
            'Negotiation': 'N',
            'Accountability': 'A',
            'Emotional Intelligence': 'EI',
            'Conflict Resolution': 'C',
            'Team Building': 'TB',
            'Servant Leadership': 'SL',
            'Adaptability': 'AD',
            'Approach to Failure': 'F',
            'Resilience and Grit': 'RG',
            'Innovation Orientation': 'IO',
            'Drive and Ambition': 'DA'
        }
        return name_to_code.get(trait_name, None)

    def _generate_comprehensive_executive_summary(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate comprehensive executive summary using LLM with open-ended responses"""
        try:
            # Extract key data
            person_name = data.get('person_name', 'Victoria Raish')
            overall_score = data.get('overall_score', 0.0)
            archetype_name = data.get('archetype_name', 'Resilient Leadership')
            archetype_score = data.get('archetype_score', 0.8)
            archetype_description = data.get('archetype_description', '')
            
            # Get trait scores for top traits
            trait_scores = data.get('trait_scores', {})
            top_traits = sorted(trait_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Get open-ended responses from the data
            open_ended_responses = data.get('open_ended_responses', {})
            
            # Create structured prompt
            prompt = f"""
            Create a professional executive summary for {person_name}'s entrepreneurial assessment report.
            
            Key Information:
            - Archetype: {archetype_name} (Score: {archetype_score:.1f})
            - Overall Score: {overall_score * 100:.1f}%
            - Top Strengths: {', '.join([self.trait_name_mapping.get(trait[0], trait[0]) for trait in top_traits])}
            
            Selected Responses:
            - Journey stage: {open_ended_responses.get('Which of the following best describes where you are in your entrepreneurial journey?', 'Not provided')}
            - Entrepreneurship definition: {open_ended_responses.get('What does "entrepreneurship" mean to you personally?', 'Not provided')}
            - What energizes them: {open_ended_responses.get('What kind of work energizes you most—and why?', 'Not provided')}
            - Future vision: {open_ended_responses.get('When you imagine your future, what role (if any) does building something yourself play?', 'Not provided')}
            - Desired impact: {open_ended_responses.get('What kind of impact do you hope your business will create—in your life or for others?', 'Not provided')}
            - What draws them: {open_ended_responses.get('What is drawing you toward entrepreneurship at this moment in your life?', 'Not provided')}
            - Initiative example: {open_ended_responses.get("What's a time when you took initiative or built something from scratch?", 'Not provided')}
            - Fears/uncertainties: {open_ended_responses.get('What fears or uncertainties do you have about starting something of your own?', 'Not provided')}
            - Success definition: {open_ended_responses.get('What would success look like for you in this phase of exploration?', 'Not provided')}
            - Entrepreneurial energy: {open_ended_responses.get('If you were to fully embrace your entrepreneurial energy, what might become possible?', 'Not provided')}
            
            STRUCTURE REQUIRED:
            
            PARAGRAPH 1 (3-4 sentences): ARCHETYPE AND REPORT OVERVIEW
            Write ONLY about:
            - The {archetype_name} archetype and how it functions in entrepreneurship
            - The practical characteristics and behaviors of this archetype
            - Overview of the comprehensive assessment report and its value
            - DO NOT mention any personal responses, quotes, or individual details
            - DO NOT use trait.txt content
            
            PARAGRAPH 2 (3-4 sentences): OPEN-ENDED RESPONSES ANALYSIS
            Write ONLY about their specific responses:
            - Analyze their specific quotes and how they connect to the archetype
            - Show how their answers demonstrate archetype characteristics
            - Provide guidance based on their specific responses
            - DO NOT describe the archetype again
            - DO NOT use trait.txt content
            
            CRITICAL RULES:
            - Paragraph 1 = Archetype and report overview only
            - Paragraph 2 = Personal responses analysis only
            - NO mixing of topics between paragraphs
            - NO repetition of words or phrases
            - Use their actual words only once
            - Be concise and professional
            - Fix grammar errors
            """
            
            if self.openai_client:
                # Generate archetype paragraph only
                clean_archetype_name = archetype_name.replace('\\', '')
                archetype_prompt = f"""
                Write a professional paragraph (3-4 sentences) about the {clean_archetype_name} archetype in entrepreneurship.
                
                Focus ONLY on:
                - What this archetype is and how it functions in entrepreneurship
                - The practical characteristics and behaviors of this archetype
                - How this archetype approaches business challenges and opportunities
                
                DO NOT mention any personal responses, quotes, or individual details.
                Be professional and concise.
                """
                
                archetype_response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert entrepreneurial coach. Write ONLY about archetypes in entrepreneurship. Do not mention personal responses or individual details."},
                        {"role": "user", "content": archetype_prompt}
                    ],
                    max_tokens=200,
                    temperature=0.3
                )
                
                # Generate personal responses paragraph only
                # Debug: Print the actual responses being used
                journey_stage = open_ended_responses.get('Which of the following best describes where you are in your entrepreneurial journey?', 'Not provided')
                entrepreneurship_def = open_ended_responses.get('What does "entrepreneurship" mean to you personally?', 'Not provided')
                what_energizes = open_ended_responses.get('What kind of work energizes you most—and why?', 'Not provided')
                future_vision = open_ended_responses.get('When you imagine your future, what role (if any) does building something yourself play?', 'Not provided')
                desired_impact = open_ended_responses.get('What kind of impact do you hope your business will create—in your life or for others?', 'Not provided')
                what_draws = open_ended_responses.get('What is drawing you toward entrepreneurship at this moment in your life?', 'Not provided')
                initiative_example = open_ended_responses.get("What's a time when you took initiative or built something from scratch?", 'Not provided')
                fears = open_ended_responses.get('What fears or uncertainties do you have about starting something of your own?', 'Not provided')
                success_def = open_ended_responses.get('What would success look like for you in this phase of exploration?', 'Not provided')
                entrepreneurial_energy = open_ended_responses.get('If you were to fully embrace your entrepreneurial energy, what might become possible?', 'Not provided')
                
                print(f"DEBUG - Journey stage: {journey_stage}")
                print(f"DEBUG - Entrepreneurship definition: {entrepreneurship_def}")
                print(f"DEBUG - What energizes: {what_energizes}")
                print(f"DEBUG - Future vision: {future_vision}")
                print(f"DEBUG - Desired impact: {desired_impact}")
                print(f"DEBUG - What draws: {what_draws}")
                print(f"DEBUG - Initiative example: {initiative_example}")
                print(f"DEBUG - Fears: {fears}")
                print(f"DEBUG - Success definition: {success_def}")
                print(f"DEBUG - Entrepreneurial energy: {entrepreneurial_energy}")
                
                personal_prompt = f"""
                Write a professional paragraph (3-4 sentences) analyzing these specific responses and how they connect to the {clean_archetype_name} archetype.
                
                ACTUAL RESPONSES TO ANALYZE:
                - Journey stage: "{journey_stage}"
                - Entrepreneurship definition: "{entrepreneurship_def}"
                - What energizes them: "{what_energizes}"
                - Future vision: "{future_vision}"
                - Desired impact: "{desired_impact}"
                - What draws them: "{what_draws}"
                - Initiative example: "{initiative_example}"
                - Fears/uncertainties: "{fears}"
                - Success definition: "{success_def}"
                - Entrepreneurial energy: "{entrepreneurial_energy}"
                
                REQUIREMENTS:
                - Use their EXACT quotes from the responses above (only use responses that are not "Not provided")
                - Show how their specific words connect to the archetype
                - Analyze their actual responses, not generic statements
                - Provide guidance based on their specific words
                
                DO NOT describe the archetype again.
                Be professional and concise.
                """
                
                personal_response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert entrepreneurial coach. Write ONLY about analyzing personal responses and how they connect to archetypes. You MUST use the exact quotes provided in the responses. Do not describe the archetype itself. Focus on their specific words and how they demonstrate archetype characteristics."},
                        {"role": "user", "content": personal_prompt}
                    ],
                    max_tokens=200,
                    temperature=0.3
                )
                
                return {
                    'paragraph1': archetype_response.choices[0].message.content.strip(),
                    'paragraph2': personal_response.choices[0].message.content.strip()
                }
            else:
                # Fallback if no OpenAI client
                return {
                    'paragraph1': f"The {archetype_name} archetype represents a strategic approach to entrepreneurial leadership, emphasizing resilience, adaptability, and sustainable growth. This archetype excels at navigating complex business challenges while maintaining team cohesion and driving long-term success. This comprehensive assessment provides detailed analysis of entrepreneurial strengths, growth opportunities, and strategic recommendations for professional development.",
                    'paragraph2': f"Your responses reveal natural alignment with {archetype_name} characteristics, particularly in your focus on meaningful impact and strategic thinking. Your definition of entrepreneurship demonstrates the archetype's core value of creating lasting value. Leverage your natural strengths to accelerate your entrepreneurial journey while addressing areas for growth identified in this assessment."
                }
                
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            # Fallback
            return {
                'paragraph1': f"{data.get('person_name', 'Victoria Raish')}, your assessment reveals a dynamic entrepreneurial profile with an overall score of {data.get('overall_score', 0.0) * 100:.1f}%. This indicates strong potential for entrepreneurial success with a balanced mix of leadership, innovation, and resilience capabilities.",
                'paragraph2': f"The {data.get('archetype_name', 'Resilient Leadership')} archetype was selected because it best matches your entrepreneurial profile and goals."
            }

    def _generate_strengths_explanation(self, trait_scores: Dict[str, float]) -> str:
        """Generate explanation for top 3 strengths shown in gauge graphs"""
        try:
            # Filter out IN (Social Orientation) from trait scores
            filtered_scores = {k: v for k, v in trait_scores.items() if k != 'IN'}
            # Get top 3 traits (same as gauge graphs, excluding IN)
            sorted_traits = sorted(filtered_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
            if not sorted_traits:
                return "Your entrepreneurial strengths are developing through continuous learning and experience."
            
            trait_names = [self.trait_name_mapping.get(trait, trait) for trait, _ in sorted_traits]
            
            # Get trait descriptions from trait.txt for strengths
            trait_descriptions = []
            for trait_code, _ in sorted_traits:
                trait_name = self.trait_name_mapping.get(trait_code, trait_code)
                description = self._get_trait_description(trait_code, 0.8)  # High score for strength
                if description:
                    trait_descriptions.append(f"{trait_name}: {description}")
            
            # Generate LLM content for these specific strengths
            if self.openai_client:
                trait_context = "\n".join(trait_descriptions) if trait_descriptions else f"Focus on these strengths: {', '.join(trait_names)}"
                
                prompt = f"""Based on these top 3 entrepreneurial strengths and their descriptions from trait.txt:

{trait_context}

Write a brief 2-3 line explanation that highlights how these specific traits work together to create entrepreneurial success. Focus on the synergy between these exact strengths and their practical impact in business contexts. Use an inspiring and professional tone that references the specific strengths mentioned in the trait descriptions."""
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=120,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            else:
                # Fallback content using trait descriptions
                if trait_descriptions:
                    return f"Your combination of {', '.join(trait_names)} creates a powerful foundation for entrepreneurial success. These strengths enable you to navigate challenges with confidence while building meaningful connections and driving innovation in your ventures."
                else:
                    return f"Your combination of {', '.join(trait_names)} creates a powerful foundation for entrepreneurial success. These strengths enable you to navigate challenges with confidence while building meaningful connections and driving innovation in your ventures."
                
        except Exception as e:
            logger.error(f"Error generating strengths explanation: {e}")
            return "Your entrepreneurial strengths provide a solid foundation for success in business and leadership contexts."

    def _generate_growth_explanation(self, trait_scores: Dict[str, float]) -> str:
        """Generate explanation for growth opportunities shown in gauge graphs"""
        try:
            # Filter out IN (Social Orientation) from trait scores
            filtered_scores = {k: v for k, v in trait_scores.items() if k != 'IN'}
            # Get bottom 3 traits (same as growth gauge graphs) - exclude top 3 to avoid duplication
            sorted_traits = sorted(filtered_scores.items(), key=lambda x: x[1])  # Sort lowest to highest
            # Get the actual bottom 3 traits with lowest scores, but exclude any that are in top 3
            top_3_traits = sorted(filtered_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            top_3_codes = [trait[0] for trait in top_3_traits]
            
            # Get the bottom 3 traits from the lowest scores, excluding top 3
            bottom_traits = []
            for trait, score in sorted_traits:
                if trait not in top_3_codes:
                    bottom_traits.append((trait, score))
                if len(bottom_traits) >= 3:
                    break
            
            # If we don't have 3 traits after filtering, take the actual bottom 3
            if len(bottom_traits) < 3:
                bottom_traits = sorted_traits[:3]
            
            if not bottom_traits:
                return "Focus on continuous development to enhance your entrepreneurial capabilities."
            
            trait_names = [self.trait_name_mapping.get(trait, trait) for trait, _ in bottom_traits]
            
            # Get trait descriptions from trait.txt for growth areas
            trait_descriptions = []
            for trait_code, _ in bottom_traits:
                trait_name = self.trait_name_mapping.get(trait_code, trait_code)
                description = self._get_trait_description(trait_code, 0.3)  # Low score for growth area
                if description:
                    trait_descriptions.append(f"{trait_name}: {description}")
            
            # Generate LLM content for these specific growth areas
            if self.openai_client:
                trait_context = "\n".join(trait_descriptions) if trait_descriptions else f"Focus on developing: {', '.join(trait_names)}"
                
                prompt = f"""Based on these growth opportunities and their descriptions from trait.txt:

{trait_context}

Write a brief 2-3 line explanation that motivates development in these specific areas. Focus on the potential impact of improving these exact traits and how they complement existing strengths. Use an encouraging and professional tone that references the specific growth potential mentioned in the trait descriptions."""
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            else:
                # Fallback content using trait descriptions
                if trait_descriptions:
                    return f"Developing these areas will strengthen your overall entrepreneurial profile: {', '.join(trait_names)}. These growth opportunities represent key areas where focused development can create more balanced leadership approaches and unlock new potential in your business endeavors."
                else:
                    return f"Developing {', '.join(trait_names)} will strengthen your overall entrepreneurial profile. These areas represent opportunities to enhance your capabilities and create more balanced leadership approaches in your business endeavors."
                
        except Exception as e:
            logger.error(f"Error generating growth explanation: {e}")
            return "Focus on developing these areas to create a more comprehensive entrepreneurial skill set."

    def _generate_individual_growth_explanations(self, trait_scores: Dict[str, float]) -> List[Dict[str, str]]:
        """Generate individual explanations for each growth trait"""
        try:
            # Filter out IN (Social Orientation) from trait scores
            filtered_scores = {k: v for k, v in trait_scores.items() if k != 'IN'}
            # Get bottom 3 traits (lowest scores) - simple approach
            sorted_traits = sorted(filtered_scores.items(), key=lambda x: x[1])  # Sort lowest to highest
            bottom_traits = sorted_traits[:3]  # Take the first 3 (lowest scores)
            
            # Debug: Print the bottom 3 traits being selected
            print(f"DEBUG - All traits sorted by score: {[(trait, round(score, 3)) for trait, score in sorted_traits]}")
            print(f"DEBUG - Bottom 3 traits selected: {[(trait, round(score, 3)) for trait, score in bottom_traits]}")
            
            if not bottom_traits:
                return []
            
            explanations = []
            for trait_code, score in bottom_traits:
                # Use the exact trait name as shown in gauge graphs
                trait_name = self.trait_name_mapping.get(trait_code, trait_code)
                
                # For growth opportunities, use the 'low' (Growth Area) descriptions from trait.txt
                if not hasattr(self, '_trait_descriptions'):
                    self._trait_descriptions = self._load_trait_descriptions()
                
                if trait_code in self._trait_descriptions:
                    description = self._trait_descriptions[trait_code]['low']  # Use Growth Area description
                else:
                    description = f"Developing {trait_name} will strengthen your entrepreneurial capabilities and create new opportunities for growth."
                
                # Use only 1-2 complete sentences from trait.txt description
                if description:
                    # Split description into complete sentences using regex
                    sentences = re.split(r'\.\s+', description)
                    
                    # Clean up sentences and ensure they end with periods
                    clean_sentences = []
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if sentence and not sentence.endswith('.'):
                            sentence += '.'
                        if sentence:
                            clean_sentences.append(sentence)
                    
                    if len(clean_sentences) >= 2:
                        # Take first 2 complete sentences
                        explanation_text = ' '.join(clean_sentences[:2])
                    elif len(clean_sentences) == 1:
                        # If only 1 complete sentence, use it
                        explanation_text = clean_sentences[0]
                    else:
                        # Fallback to original description
                        explanation_text = description
                else:
                    # Fallback explanation using exact trait name
                    explanation_text = f"Developing {trait_name} will strengthen your entrepreneurial capabilities and create new opportunities for growth."
                
                explanations.append({
                    'trait_name': trait_name,
                    'explanation': explanation_text
                })
            
            return explanations
                
        except Exception as e:
            logger.error(f"Error generating individual growth explanations: {e}")
            return []

    def _get_trait_description(self, trait_code: str, score: float) -> str:
        """Get trait description based on score and trait code using detailed descriptions from trait.txt"""
        # Load trait descriptions if not already loaded
        if not hasattr(self, '_trait_descriptions'):
            self._trait_descriptions = self._load_trait_descriptions()
        
        # Special handling for IN trait (Social Orientation)
        if trait_code == 'IN':
            if trait_code in self._trait_descriptions:
                # Select description based on score threshold (0.5)
                if score >= 0.5:
                    # High score = Extroversion
                    full_description = self._trait_descriptions[trait_code].get('high_extro', '')
                else:
                    # Low score = Introversion
                    full_description = self._trait_descriptions[trait_code].get('high_intro', '')
                
                if full_description.strip():
                    # Only vary the first sentence using LLM, keep rest from trait.txt
                    if self.openai_client:
                        return self._vary_first_sentence_only(trait_code, score, full_description)
                    else:
                        return full_description
                else:
                    # Fallback if descriptions not found
                    return f"Your {self.trait_name_mapping.get(trait_code, trait_code)} score is {round(score * 100, 1)}%."
            else:
                return f"Your {self.trait_name_mapping.get(trait_code, trait_code)} score is {round(score * 100, 1)}%."
        
        # For all other traits, use the standard 'high' (Strength) description
        level = 'high'
        
        # Get description for trait code
        if trait_code in self._trait_descriptions:
            full_description = self._trait_descriptions[trait_code].get(level, '')
            
            # Only vary the first sentence using LLM, keep rest from trait.txt
            if full_description.strip():
                if self.openai_client:
                    return self._vary_first_sentence_only(trait_code, score, full_description)
                else:
                    return full_description
            else:
                return f"Your {self.trait_name_mapping.get(trait_code, trait_code)} score is {round(score * 100, 1)}%."
        else:
            # Fallback to basic description
            return f"Your {self.trait_name_mapping.get(trait_code, trait_code)} score is {round(score * 100, 1)}%."
    
    def _vary_first_sentence_only(self, trait_code: str, score: float, full_description: str) -> str:
        """Only vary the first sentence of trait description, keep rest from trait.txt"""
        try:
            trait_name = self.trait_name_mapping.get(trait_code, trait_code)
            score_percentage = round(score * 100, 1)
            
            # Split description into sentences
            sentences = full_description.split('. ')
            if len(sentences) < 2:
                # If only one sentence, return as is
                return full_description
            
            first_sentence = sentences[0].strip()
            remaining_text = '. '.join(sentences[1:]).strip()
            
            # Ensure remaining text ends with period
            if remaining_text and not remaining_text.endswith('.'):
                remaining_text += '.'
            
            # Generate simple first sentence only
            prompt = f"""Create a simple, clear first sentence for this trait description. Keep it straightforward and professional.

Trait: {trait_name}
Score: {score_percentage}%
Original First Sentence: {first_sentence}

Requirements:
- EXACTLY one sentence only
- Keep the same meaning and key points
- Make it simple and clear
- Avoid complex or flowery language
- End with a period
- Keep it professional

Generate ONLY the first sentence:"""

            response = self.openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=30,
                temperature=0.3
            )
            
            new_first_sentence = response.choices[0].message.content.strip()
            
            # Ensure it ends with period
            if not new_first_sentence.endswith('.'):
                new_first_sentence += '.'
            
            # Combine new first sentence with original remaining text
            return f"{new_first_sentence} {remaining_text}"
            
        except Exception as e:
            logger.error(f"Error varying first sentence for {trait_code}: {e}")
            return full_description  # Fallback to original description
    
    def _generate_archetype_activation_description(self, archetype_name: str) -> str:
        """Generate archetype-specific activation description"""
        try:
            if self.openai_client:
                clean_archetype_name = archetype_name.replace('\\', '')
                prompt = f"""Create a personalized activation description for the {clean_archetype_name} archetype. Use this exact format and structure:

Your results confirm your strength as a {clean_archetype_name} — someone who [specific qualities and characteristics of this archetype]. These qualities position you to [how these qualities help in leadership/entrepreneurship], turning [challenges] into [opportunities] and [obstacles] into [positive outcomes].

The next step is to activate these strengths through Vertria Vantage — a dynamic experience that transforms insights into practice. Here you'll engage in challenges that [specific activities for this archetype], expand your ability to [relevant skills], and translate your purpose into tangible strategies. You'll also step into a trusted network of peers and mentors who will walk beside you as you grow.

Don't stop at insight. Step into Vertria Vantage, the next stage of your journey where your assessment comes alive — connecting you with the right opportunities, mentors, and challenges to activate your entrepreneurial advantage.

Requirements:
- Keep the exact structure and flow
- Make it specific to the {archetype_name} archetype
- Use dynamic, engaging language
- Focus on the unique strengths of this archetype
- Keep it professional and inspiring

Generate the activation description:"""

                response = self.openai_client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.7
                )
                
                return response.choices[0].message.content.strip()
            else:
                # Fallback description
                clean_archetype_name = archetype_name.replace('\\', '')
                return f"""Your results confirm your strength as a {clean_archetype_name} — someone who not only adapts and perseveres but also sees connections others often miss and pursues a vision rooted in making a difference rather than simply building something. These qualities position you to lead with both clarity and purpose, turning uncertainty into opportunity and setbacks into momentum.

The next step is to activate these strengths through Vertria Vantage — a dynamic experience that transforms insights into practice. Here you'll engage in challenges that sharpen resilience, expand your ability to connect people and ideas, and translate your purpose into tangible strategies. You'll also step into a trusted network of peers and mentors who will walk beside you as you grow.

Don't stop at insight. Step into Vertria Vantage, the next stage of your journey where your assessment comes alive — connecting you with the right opportunities, mentors, and challenges to activate your entrepreneurial advantage."""
                
        except Exception as e:
            logger.error(f"Error generating archetype activation description: {e}")
            # Fallback description
            clean_archetype_name = archetype_name.replace('\\', '')
            return f"""Your results confirm your strength as a {clean_archetype_name} — someone who not only adapts and perseveres but also sees connections others often miss and pursues a vision rooted in making a difference rather than simply building something. These qualities position you to lead with both clarity and purpose, turning uncertainty into opportunity and setbacks into momentum.

The next step is to activate these strengths through Vertria Vantage — a dynamic experience that transforms insights into practice. Here you'll engage in challenges that sharpen resilience, expand your ability to connect people and ideas, and translate your purpose into tangible strategies. You'll also step into a trusted network of peers and mentors who will walk beside you as you grow.

Don't stop at insight. Step into Vertria Vantage, the next stage of your journey where your assessment comes alive — connecting you with the right opportunities, mentors, and challenges to activate your entrepreneurial advantage."""
    
    
    def generate_comprehensive_report(self, data: Dict[str, Any], output_path: str) -> Dict[str, Any]:
        """Generate comprehensive HTML report"""
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Prepare traits data for template
            trait_scores = data.get('trait_scores', {})
            traits = []
            for trait_code, score in trait_scores.items():
                trait_name = self.trait_name_mapping.get(trait_code, trait_code)
                trait_description = self._get_trait_description(trait_code, score)
                is_low_score = score < 0.6  # Below 60%
                traits.append({
                    'code': trait_name,  # Use full name instead of abbreviation
                    'name': trait_name,
                    'score': score,
                    'percentage': round(score * 100, 1),
                    'description': trait_description,
                    'is_low_score': is_low_score,
                    'css_class': 'low-score' if is_low_score else ''
                })
            
            # Sort traits by score (highest first)
            traits.sort(key=lambda x: x['score'], reverse=True)
            
            # Create prioritized Key Traits list: Social Orientation FIRST, then archetype key traits
            from victoria.core.archetype_detector import ArchetypeDetector
            detector = ArchetypeDetector()
            archetype_name = data.get('archetype_name', 'Resilient Leadership')
            
            # Find the archetype object
            archetype_obj = None
            for arch_id, arch in detector.archetypes.items():
                if arch.name == archetype_name:
                    archetype_obj = arch
                    break
            
            # Create prioritized traits list for Key Traits section
            key_traits_for_section = []
            
            # STEP 1: ALWAYS add Social Orientation FIRST (trait code 'IN')
            if 'IN' in trait_scores:
                social_orientation_score = trait_scores['IN']
                social_orientation_name = self.trait_name_mapping.get('IN', 'Social Orientation')
                social_orientation_description = self._get_trait_description('IN', social_orientation_score)
                key_traits_for_section.append({
                    'code': social_orientation_name,
                    'name': social_orientation_name,
                    'score': social_orientation_score,
                    'percentage': round(social_orientation_score * 100, 1),
                    'description': social_orientation_description,
                    'is_low_score': social_orientation_score < 0.6,
                    'css_class': 'low-score' if social_orientation_score < 0.6 else '',
                    'is_key_trait': False,  # Not technically a key trait, but always shown
                    'is_social_orientation': True  # Flag to identify this special trait
                })
            
            # STEP 2: Add archetype key traits (up to 3 more, for total of 4)
            if archetype_obj:
                # Map archetype key trait names to trait codes
                key_trait_codes = []
                for key_trait_name in archetype_obj.key_traits:
                    trait_code = detector.trait_name_to_code.get(key_trait_name)
                    if trait_code and trait_code != 'IN':  # Exclude IN since we already added it
                        key_trait_codes.append(trait_code)
                
                # Get trait data for key traits, sorted by score (highest first)
                archetype_key_traits_data = []
                for trait_code in key_trait_codes:
                    if trait_code in trait_scores:
                        trait_name = self.trait_name_mapping.get(trait_code, trait_code)
                        score = trait_scores[trait_code]
                        trait_description = self._get_trait_description(trait_code, score)
                        archetype_key_traits_data.append({
                            'code': trait_name,
                            'name': trait_name,
                            'score': score,
                            'percentage': round(score * 100, 1),
                            'description': trait_description,
                            'is_low_score': score < 0.6,
                            'css_class': 'low-score' if score < 0.6 else '',
                            'is_key_trait': True
                        })
                
                # Sort archetype key traits by score (highest first) and take top 3
                archetype_key_traits_data.sort(key=lambda x: x['score'], reverse=True)
                key_traits_for_section.extend(archetype_key_traits_data[:3])
                
                # If we have fewer than 4 total traits (including Social Orientation), 
                # fill remaining slots with highest-scoring non-key traits
                if len(key_traits_for_section) < 4:
                    remaining_slots = 4 - len(key_traits_for_section)
                    existing_codes = [t['code'] for t in key_traits_for_section]
                    non_key_traits = [t for t in traits if t['code'] not in existing_codes]
                    key_traits_for_section.extend(non_key_traits[:remaining_slots])
                
                data['key_traits'] = key_traits_for_section[:4]  # Ensure max 4 traits
            else:
                # Fallback: Social Orientation + top 3 by score if archetype not found
                if 'IN' in trait_scores:
                    # Social Orientation already added above, get remaining traits
                    social_orientation_name = self.trait_name_mapping.get('IN', 'Social Orientation')
                    remaining_traits = [t for t in traits if t['code'] != social_orientation_name]
                    key_traits_for_section.extend(remaining_traits[:3])
                else:
                    # If IN not found, just use top 4 by score
                    key_traits_for_section = traits[:4]
                data['key_traits'] = key_traits_for_section[:4]
            
            # Add traits data to template data
            data['traits'] = traits
            
            # Add growth gauges chart
            if 'growth_gauges_chart' in data:
                data['growth_trait_gauges'] = data['growth_gauges_chart']
            
            # Generate trait explanations for strengths and growth opportunities
            data['strengths_explanation'] = self._generate_strengths_explanation(trait_scores)
            data['growth_explanation'] = self._generate_growth_explanation(trait_scores)
            
            # Generate individual growth trait explanations
            data['growth_trait_explanations'] = self._generate_individual_growth_explanations(trait_scores)
            
            # Generate archetype activation description
            data['archetype_activation_description'] = self._generate_archetype_activation_description(data.get('archetype_name', 'Resilient Leadership'))
            
            # Add entrepreneurial stage data
            data['entrepreneurial_stage'] = data.get('entrepreneurial_stage', 'Discover')
            data['entrepreneurial_stage_description'] = data.get('entrepreneurial_stage_description', 
                'You want to understand how entrepreneurial energy shapes your path. This stage is about self-discovery, building awareness, and connecting your natural strengths to potential opportunities.')
            
            # Add Next Steps content
            data['next_steps_description'] = data.get('next_steps_description', 
                "You're uncovering how entrepreneurial energy shapes your personal and professional path. This phase is about self-discovery and connecting the dots between who you are and what you could build.")
            
            data['vantage_description'] = data.get('vantage_description',
                "Think of us as your guide through uncharted territory. We'll help you uncover how your energy, skills, and passions can align with entrepreneurial opportunities.")
            
            data['mentors_description'] = data.get('mentors_description',
                "Connect with leaders who use entrepreneurial thinking in diverse careers — not just startups. Their guidance can show you how entrepreneurship is a mindset as much as a career choice.")
            
            data['community_items'] = data.get('community_items', [
                {"title": "Courses", "description": "Exploratory programs on leadership, creativity, and durable skills."},
                {"title": "Events", "description": "Community conversations about resilience, adaptability, and vision."},
                {"title": "Networking", "description": "Broader networks that encourage you to experiment with different roles and directions."}
            ])
            
            # Generate comprehensive executive summary using LLM
            executive_summary = self._generate_comprehensive_executive_summary(data)
            data['executive_summary_paragraph1'] = executive_summary['paragraph1']
            data['executive_summary_paragraph2'] = executive_summary['paragraph2']
            
            # Load template
            template_dir = os.path.dirname(self.template_path)
            template_name = os.path.basename(self.template_path)
            env = Environment(loader=FileSystemLoader(template_dir))
            template = env.get_template(template_name)
            
            # Render template
            html_content = template.render(**data)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Report generated successfully: {output_path}")
            return {'success': True, 'file_path': output_path}
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {'success': False, 'error': str(e)}