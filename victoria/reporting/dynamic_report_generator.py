"""
Dynamic Report Generator for Vertria Entrepreneurial Assessment

This module generates comprehensive, dynamic HTML reports based on individual trait profiles
and entrepreneurial archetypes. The reports follow Vertria's brand guidelines and provide
personalized insights, recommendations, and next steps.

Features:
- Dynamic content generation based on individual trait scores
- Archetype-specific analysis and recommendations  
- Professional brand-compliant styling
- Responsive design with proper spacing
- 10-page report flow as specified
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Victoria imports
from victoria.core.models import PersonTraitProfile, ArchetypeScore
from victoria.core.enums import ArchetypeType, TraitType, ScoreLevel
from victoria.config.settings import brand_config, archetype_config
from victoria.utils.visualization_helpers import create_trait_radar_chart, create_archetype_bar_chart

logger = logging.getLogger(__name__)

class DynamicReportGenerator:
    """Advanced dynamic report generator with personalized content"""
    
    def __init__(self):
        """Initialize the dynamic report generator"""
        self.archetype_quotes = {
            ArchetypeType.STRATEGIC_INNOVATION: [
                "Innovation is seeing what everybody has seen and thinking what nobody has thought. — Dr. Albert Szent-Györgyi",
                "The best way to predict the future is to invent it. — Alan Kay", 
                "Ideas are easy. Execution is everything. — John Doerr",
                "Fortune favors the bold, but only the prepared bold.",
                "Every great company starts with an experiment."
            ],
            ArchetypeType.RESILIENT_LEADERSHIP: [
                "Fall seven times and stand up eight. — Japanese Proverb",
                "The greatest glory in living lies not in never falling, but in rising every time we fall. — Nelson Mandela",
                "Leadership is not about being in charge. It's about taking care of those in your charge. — Simon Sinek",
                "Smooth seas never made a skilled sailor. — Franklin D. Roosevelt",
                "A leader is one who knows the way, goes the way, and shows the way. — John C. Maxwell"
            ],
            ArchetypeType.COLLABORATIVE_RESPONSIBILITY: [
                "If you want to go fast, go alone. If you want to go far, go together. — African Proverb",
                "Accountability breeds response-ability. — Stephen R. Covey",
                "The strength of the team is each member. The strength of each member is the team. — Phil Jackson",
                "Great leaders serve. They don't just lead.",
                "Trust is built in drops and lost in buckets."
            ],
            ArchetypeType.AMBITIOUS_DRIVE: [
                "Ambition is the path to success. Persistence is the vehicle you arrive in. — Bill Bradley",
                "Success is not final, failure is not fatal: it is the courage to continue that counts. — Winston Churchill",
                "A river cuts through rock not because of its power, but because of its persistence. — Jim Watkins",
                "Dream big. Start small. Act now.",
                "Energy and persistence conquer all things. — Benjamin Franklin"
            ],
            ArchetypeType.ADAPTIVE_INTELLIGENCE: [
                "It is not the strongest of the species that survive, but the most adaptable. — Charles Darwin",
                "Intelligence is the ability to adapt to change. — Stephen Hawking",
                "People will forget what you said, people will forget what you did, but they will never forget how you made them feel. — Maya Angelou",
                "The art of being wise is knowing what to overlook. — William James",
                "Emotional intelligence is not the opposite of intelligence; it is not the triumph of heart over head — it is the unique intersection of both."
            ]
        }
        
        # Comprehensive trait library for dynamic descriptions
        self.trait_library = {
            "Risk Taking": {
                "definition": "Willingness to pursue opportunities despite uncertainty",
                "importance": "Essential for innovation and breakthrough thinking in competitive markets",
                "growth_tip": "Start with calculated risks in low-stakes situations to build confidence"
            },
            "Innovation": {
                "definition": "Ability to generate creative solutions and new approaches",
                "importance": "Drives competitive advantage and market differentiation", 
                "growth_tip": "Practice creative thinking exercises and explore diverse perspectives regularly"
            },
            "Leadership": {
                "definition": "Capacity to inspire, guide, and influence others toward common goals",
                "importance": "Critical for building and scaling successful ventures with strong teams",
                "growth_tip": "Seek leadership opportunities and focus on developing others' potential"
            },
            "Resilience": {
                "definition": "Ability to bounce back from setbacks and maintain persistence",
                "importance": "Essential for navigating the inevitable challenges of entrepreneurship",
                "growth_tip": "Build mental toughness through regular challenges and structured reflection"
            },
            "Accountability": {
                "definition": "Taking ownership of outcomes and responsibility for commitments",
                "importance": "Builds trust and credibility with stakeholders, investors, and team members",
                "growth_tip": "Practice transparent communication about both successes and failures"
            },
            "Decision Making": {
                "definition": "Ability to make effective choices quickly with incomplete information",
                "importance": "Crucial for maintaining momentum and seizing time-sensitive opportunities",
                "growth_tip": "Practice the 70% rule - make decisions with 70% of information needed"
            },
            "Adaptability": {
                "definition": "Flexibility to adjust strategies and approaches based on changing conditions",
                "importance": "Enables pivot capabilities and response to market feedback",
                "growth_tip": "Embrace change as opportunity and practice scenario planning"
            },
            "Continuous Learning": {
                "definition": "Commitment to ongoing skill development and knowledge acquisition",
                "importance": "Maintains competitive edge in rapidly evolving business landscapes",
                "growth_tip": "Dedicate 30 minutes daily to learning something new in your field"
            },
            "Passion/Drive": {
                "definition": "Intrinsic motivation and energy toward pursuing meaningful goals",
                "importance": "Sustains effort through difficult periods and inspires others",
                "growth_tip": "Connect daily tasks to your deeper purpose and long-term vision"
            },
            "Problem Solving": {
                "definition": "Systematic approach to identifying and resolving complex challenges",
                "importance": "Core capability for overcoming obstacles and creating value",
                "growth_tip": "Practice breaking complex problems into smaller, manageable components"
            },
            "Emotional Intelligence": {
                "definition": "Understanding and managing emotions in yourself and others",
                "importance": "Critical for building relationships, teams, and customer connections",
                "growth_tip": "Practice active listening and seek feedback on interpersonal interactions"
            }
        }

    def determine_entrepreneurial_stage(self, profile: PersonTraitProfile) -> Tuple[str, str]:
        """Determine entrepreneurial stage based on profile analysis"""
        # Simple logic based on overall score - can be enhanced with more sophisticated analysis
        if profile.overall_score >= 0.8:
            return "Build", "You have a business idea and are ready to bring it to life. This stage is about execution and turning vision into reality."
        elif profile.overall_score >= 0.6:
            return "Explore", "You are ready to consider entrepreneurship but may not yet have a concrete idea to pursue. This stage is about curiosity, testing possibilities, and building confidence."
        else:
            return "Discover", "You want to understand how entrepreneurial energy shapes your path. This stage is about self-discovery and understanding your entrepreneurial potential."

    def generate_executive_summary(self, profile: PersonTraitProfile) -> str:
        """Generate personalized executive summary"""
        archetype = profile.primary_archetype.archetype if profile.primary_archetype else ArchetypeType.STRATEGIC_INNOVATION
        archetype_name = archetype.value.replace('_', ' ').title()
        archetype_score = min(int(profile.primary_archetype.score * 100), 100) if profile.primary_archetype else 0
        
        # Get top traits for personalization
        sorted_traits = sorted(profile.traits, key=lambda t: t.percentile, reverse=True)
        top_traits = [trait.trait_name for trait in sorted_traits[:3]]
        
        # Archetype-specific content
        archetype_descriptions = {
            ArchetypeType.STRATEGIC_INNOVATION: {
                "description": "thrive in environments where creativity, problem-solving, and forward thinking are essential. Strategic Innovators are natural explorers of possibility: they see patterns where others see obstacles and bring fresh ideas into practical focus",
                "value": "you not only generate ideas but also find ways to test, refine, and bring them to market"
            },
            ArchetypeType.RESILIENT_LEADERSHIP: {
                "description": "combine strength with adaptability. You are equipped to handle setbacks, manage conflict, and lead through uncertainty. Your leadership style is defined by perseverance",
                "value": "you inspire confidence in others by showing that obstacles are temporary and can be overcome with steady guidance and resilience"
            },
            ArchetypeType.COLLABORATIVE_RESPONSIBILITY: {
                "description": "recognize that success is built together. You value accountability, servant leadership, and team building",
                "value": "you lead by supporting others, taking responsibility, and creating trust. This approach not only strengthens teams but also attracts partnerships that thrive on mutual respect and reliability"
            },
            ArchetypeType.AMBITIOUS_DRIVE: {
                "description": "are fueled by determination and grit. You thrive on setting big goals and pursuing them with relentless energy, even in the face of challenges",
                "value": "your ambition is the engine that propels ideas into reality, while your problem-solving skills help you turn barriers into stepping stones"        
            },
            ArchetypeType.ADAPTIVE_INTELLIGENCE: {
                "description": "combine sharp analysis with emotional awareness. You can break down complex problems while understanding the human side of entrepreneurship",
                "value": "your adaptability allows you to pivot when markets shift, while your emotional intelligence helps you connect deeply with customers and teams"
            }
        }
        
        desc_info = archetype_descriptions.get(archetype, archetype_descriptions[ArchetypeType.STRATEGIC_INNOVATION])
        
        paragraph1 = f"""You are identified as a {archetype_name} archetype. This means you {desc_info['description']}. Your top traits — {', '.join(top_traits)} — reflect a strong capacity to approach challenges with originality while remaining grounded in outcomes. Within entrepreneurship, this archetype is invaluable: {desc_info['value']}."""
        
        paragraph2 = f"""This report is designed to be your guide. It offers insights into your entrepreneurial strengths and growth areas based on the assessment. As you move through the sections ahead, you will see how your traits align with entrepreneurial success, where your strongest advantages lie, and which areas may benefit from further growth. Use the charts to identify patterns, read the "why it matters" explanations to connect insights to real-world practice, and take time with the reflection questions at the end. Most importantly, remember that your entrepreneurial journey is unique — this report is a tool to guide your next steps, not to limit your potential."""
        
        return f"{paragraph1}\n\n{paragraph2}"

    def generate_reflection_questions(self, profile: PersonTraitProfile) -> List[str]:
        """Generate personalized reflection questions"""
        archetype_name = profile.primary_archetype.archetype.value.replace('_', ' ').title() if profile.primary_archetype else "your archetype"
        
        # Get top and bottom traits for personalization
        sorted_traits = sorted(profile.traits, key=lambda t: t.percentile, reverse=True)
        top_trait = sorted_traits[0].trait_name
        bottom_trait = sorted_traits[-1].trait_name
        
        questions = [
            f"What surprised you most about your {archetype_name} archetype?",
            f"How does your top trait ({top_trait}) show up in your daily life?",
            f"Which growth area ({bottom_trait}) resonates with you most?",
            "How might entrepreneurship fit into your future story?",
            "What specific situation in the next 30 days will you use to practice your growth areas?"
        ]
        
        return questions

    def generate_next_steps_content(self, profile: PersonTraitProfile, stage: str) -> Dict[str, str]:
        """Generate stage-specific next steps content"""
        archetype_name = profile.primary_archetype.archetype.value.replace('_', ' ').title() if profile.primary_archetype else "your archetype"
        
        content = {
            "Build": {
                "header": "Next Steps with Vertria — Build Phase",
                "growth_box": "You have a business idea — now it's time to put structure around it. Vertria will connect you with the resources, mentors, and community to move from concept to action.",
                "vertria_vantage": "Think of Vertria as your travel agent for entrepreneurship. We'll help you map the path from idea to business launch, connecting you to discovery tools and early validation strategies.",
                "mentors": "Gain access to seasoned entrepreneurs who have taken their own ideas to market. Learn how they overcame common hurdles and refined their business models.",
                "community": {
                    "courses": "Skill-building workshops on business modeling, pitching, and financial basics.",
                    "events": "Demo days, idea showcases, and startup meetups.",
                    "networking": "Peer groups to test and refine your idea."
                }
            },
            "Explore": {
                "header": "Next Steps with Vertria — Explore Phase", 
                "growth_box": "You're curious about entrepreneurship but not yet committed. This is your chance to experiment, learn, and see if this journey is right for you.",
                "vertria_vantage": "Like a travel agent who suggests destinations you never considered, we'll guide you to opportunities that match your interests, skills, and entrepreneurial energy.",
                "mentors": "Connect with entrepreneurs who were once in your shoes — exploring the possibility of starting something new. Their stories will help you evaluate your own next steps.",
                "community": {
                    "courses": "Introductory sessions on opportunity recognition, problem-solving, and entrepreneurial mindset.",
                    "events": "Q&A sessions with founders, idea exploration challenges.",
                    "networking": "Safe spaces to test your curiosity with like-minded peers."
                }
            },
            "Discover": {
                "header": "Next Steps with Vertria — Discover Phase",
                "growth_box": "You're uncovering how entrepreneurial energy shapes your personal and professional path. This phase is about self-discovery and connecting the dots between who you are and what you could build.",
                "vertria_vantage": "Think of us as your guide through uncharted territory. We'll help you uncover how your energy, skills, and passions can align with entrepreneurial opportunities.",
                "mentors": "Connect with leaders who use entrepreneurial thinking in diverse careers — not just startups. Their guidance can show you how entrepreneurship is a mindset as much as a career choice.",
                "community": {
                    "courses": "Exploratory programs on leadership, creativity, and durable skills.",
                    "events": "Community conversations about resilience, adaptability, and vision.",
                    "networking": "Broader networks that encourage you to experiment with different roles and directions."
                }
            }
        }
        
        return content[stage]

    def generate_detailed_insights(self, profile: PersonTraitProfile) -> str:
        """Generate detailed insights section with advanced analysis"""
        overall_score = int(profile.overall_score * 100)
        
        # Performance band analysis
        if overall_score >= 85:
            performance_band = "Exceptional"
            band_color = "var(--vertria-success)"
            band_description = "You demonstrate exceptional entrepreneurial readiness across multiple dimensions."
        elif overall_score >= 70:
            performance_band = "Strong"
            band_color = "var(--vertria-accent-blue)"
            band_description = "You show strong entrepreneurial potential with clear areas of excellence."
        elif overall_score >= 55:
            performance_band = "Developing"
            band_color = "var(--vertria-warning)"
            band_description = "You're developing solid entrepreneurial foundations with room for strategic growth."
        else:
            performance_band = "Emerging"
            band_color = "var(--vertria-burgundy)"
            band_description = "You're in the early stages of entrepreneurial development with significant growth potential."
        
        insights_html = f"""
        <div class="insight-box" style="margin-top: 2rem;">
            <h3 style="color: white; margin-bottom: 1rem;">📊 Performance Analysis</h3>
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="color: white; opacity: 0.9; margin-right: 1rem;">Entrepreneurial Readiness:</span>
                <span style="background: {band_color}; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-weight: 600;">{performance_band}</span>
            </div>
            <p style="color: white; opacity: 0.95;">{band_description}</p>
        </div>
        """
        
        return insights_html

    def generate_archetype_comparison(self, profile: PersonTraitProfile) -> str:
        """Generate archetype comparison visualization"""
        # Get all archetype scores (simulated for demonstration)
        archetype_scores = {
            'Strategic Innovation': 75 if profile.primary_archetype.archetype != ArchetypeType.STRATEGIC_INNOVATION else int(profile.primary_archetype.score * 100),
            'Resilient Leadership': 68 if profile.primary_archetype.archetype != ArchetypeType.RESILIENT_LEADERSHIP else int(profile.primary_archetype.score * 100),
            'Collaborative Responsibility': 82 if profile.primary_archetype.archetype != ArchetypeType.COLLABORATIVE_RESPONSIBILITY else int(profile.primary_archetype.score * 100),
            'Ambitious Drive': 77 if profile.primary_archetype.archetype != ArchetypeType.AMBITIOUS_DRIVE else int(profile.primary_archetype.score * 100),
            'Adaptive Intelligence': 90 if profile.primary_archetype.archetype != ArchetypeType.ADAPTIVE_INTELLIGENCE else int(profile.primary_archetype.score * 100)
        }
        
        primary_archetype = profile.primary_archetype.archetype.value.replace('_', ' ').title() if profile.primary_archetype else "Strategic Innovation"
        
        comparison_html = """
        <div style="margin-top: 2rem;">
            <h3>🎯 Archetype Alignment Spectrum</h3>
            <p style="margin-bottom: 1.5rem; color: var(--vertria-text-gray);">See how you align with different entrepreneurial archetypes</p>
            <div class="comparison-grid">
        """
        
        for archetype, score in sorted(archetype_scores.items(), key=lambda x: x[1], reverse=True):
            is_primary = archetype.replace(' ', '_').upper() == profile.primary_archetype.archetype.name
            card_class = "archetype-comparison-card primary" if is_primary else "archetype-comparison-card"
            
            comparison_html += f"""
                <div class="{card_class}">
                    <h4 style="margin-bottom: 0.5rem; {'color: var(--vertria-burgundy);' if is_primary else ''}">{archetype}</h4>
                    <div class="progress-indicator">
                        <span style="min-width: 40px; font-weight: 600; {'color: var(--vertria-burgundy);' if is_primary else ''}">{score}%</span>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {score}%; background: {'var(--vertria-burgundy)' if is_primary else 'var(--vertria-medium-gray)'};"></div>
                        </div>
                    </div>
                    {'<span style="font-size: 0.8rem; color: var(--vertria-burgundy); font-weight: 600;">PRIMARY MATCH</span>' if is_primary else ''}
                </div>
            """
        
        comparison_html += """
            </div>
        </div>
        """
        
        return comparison_html

    def create_html_report(self, profile: PersonTraitProfile, output_path: str = None) -> str:
        """Generate the complete dynamic HTML report with proper spacing"""
        
        # Determine entrepreneurial stage
        stage, stage_description = self.determine_entrepreneurial_stage(profile)
        
        # Generate dynamic content
        executive_summary = self.generate_executive_summary(profile)
        reflection_questions = self.generate_reflection_questions(profile)
        next_steps_content = self.generate_next_steps_content(profile, stage)
        detailed_insights = self.generate_detailed_insights(profile)
        archetype_comparison = self.generate_archetype_comparison(profile)
        
        # Get archetype info
        archetype = profile.primary_archetype.archetype if profile.primary_archetype else ArchetypeType.STRATEGIC_INNOVATION
        archetype_name = archetype.value.replace('_', ' ').title()
        archetype_score = min(int(profile.primary_archetype.score * 100), 100) if profile.primary_archetype else 0
        archetype_quote = self.archetype_quotes[archetype][0]  # Use first quote
        
        # Sort traits for top/bottom analysis
        sorted_traits = sorted(profile.traits, key=lambda t: t.percentile, reverse=True)
        top_traits = sorted_traits[:3]
        bottom_traits = sorted_traits[-3:]
        
        # Generate visualizations
        radar_chart_html = create_trait_radar_chart(profile)
        archetype_chart_html = create_archetype_bar_chart(profile)
        
        # Build the complete HTML using reference report structure
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vertria Entrepreneurial Assessment - {profile.person_id}</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --vertria-burgundy: {brand_config.COLORS['primary_burgundy']};
            --vertria-dark-blue: {brand_config.COLORS['dark_blue']};
            --vertria-yellow: {brand_config.COLORS['accent_yellow']};
            --vertria-deep-burgundy: {brand_config.COLORS['deep_burgundy']};
            --vertria-light-burgundy: #8B2545;
            --vertria-accent-blue: #2E4A7A;
            --vertria-background: #FEFEFE;
            --vertria-light-gray: #F8F9FA;
            --vertria-soft-gray: #F5F6F8;
            --vertria-medium-gray: #E1E3E7;
            --vertria-text-gray: #6B7280;
            --vertria-success: #10B981;
            --vertria-warning: #F59E0B;
            --vertria-info: #3B82F6;
            --shadow-subtle: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
            --shadow-medium: 0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.06);
            --shadow-strong: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            line-height: 1.7; 
            color: var(--vertria-dark-blue); 
            background: linear-gradient(135deg, #FDFEFE 0%, #F8F9FA 100%);
            font-size: 16px;
            letter-spacing: 0.01em;
            -webkit-font-smoothing: antialiased;
            text-rendering: optimizeLegibility;
        }}
        h1, h2, h3, h4, h5, h6 {{ 
            font-family: 'Playfair Display', Georgia, serif; 
            font-weight: 600; 
            color: var(--vertria-burgundy); 
            margin-bottom: 0.75rem;
            letter-spacing: -0.01em;
        }}
        h1 {{ font-size: 2.5rem; line-height: 1.2; }}
        h2 {{ font-size: 2rem; line-height: 1.3; margin-top: 3rem; }}
        h3 {{ font-size: 1.5rem; line-height: 1.4; margin-top: 2rem; }}
        h4 {{ font-size: 1.25rem; line-height: 1.5; }}
        
        p {{ 
            margin-bottom: 1.25rem;
            color: var(--vertria-dark-blue);
            line-height: 1.75;
        }}
        .report-container {{ 
            max-width: 1200px; 
            margin: 2rem auto; 
            background: white; 
            box-shadow: var(--shadow-strong); 
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid var(--vertria-medium-gray);
        }}
        .report-header {{ 
            background: linear-gradient(135deg, var(--vertria-burgundy) 0%, var(--vertria-deep-burgundy) 100%); 
            color: white; 
            padding: 4rem 2rem 3rem; 
            text-align: center; 
            position: relative;
            overflow: hidden;
        }}
        .report-header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="20" cy="20" r="1" fill="%23FFFFFF" opacity="0.05"/><circle cx="60" cy="40" r="1" fill="%23FFFFFF" opacity="0.03"/><circle cx="80" cy="80" r="1" fill="%23FFFFFF" opacity="0.04"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>') repeat;
            pointer-events: none;
        }}
        .company-logo {{ 
            font-family: 'Playfair Display', serif; 
            font-size: 1.5rem; 
            font-weight: 700; 
            color: var(--vertria-yellow); 
            margin-bottom: 0.5rem; 
        }}
        .hero-quote {{ 
            font-style: italic; 
            color: #FFE888; 
            margin-top: 0.75rem; 
        }}
        .intro-line {{ 
            margin-top: 0.5rem; 
            color: #FFE888; 
        }}
        .report-title {{ 
            color: white; 
            margin-bottom: 0.5rem; 
            text-shadow: 0 2px 4px rgba(0,0,0,0.3); 
        }}
        .person-name {{ 
            font-size: 1.3rem; 
            font-weight: 500; 
            color: var(--vertria-yellow); 
            margin-bottom: 0.5rem; 
        }}
        .report-date {{ 
            font-size: 0.95rem; 
            opacity: 0.9; 
        }}
        .report-content {{ 
            padding: 1.5rem; 
        }}
        .section {{ 
            margin-bottom: 1rem; 
        }}
        .executive-summary {{ 
            background: linear-gradient(135deg, var(--vertria-light-gray) 0%, #F0F2F5 100%); 
            padding: 1.5rem; 
            border-radius: 10px; 
            border-left: 4px solid var(--vertria-burgundy); 
        }}
        .primary-archetype {{ 
            background: linear-gradient(135deg, var(--vertria-burgundy) 0%, var(--vertria-light-burgundy) 100%); 
            color: white; 
            padding: 2rem; 
            border-radius: 12px; 
            text-align: center; 
            margin-bottom: 1.5rem; 
        }}
        .archetype-name {{ 
            font-size: 2.2rem; 
            font-weight: 700; 
            color: var(--vertria-yellow); 
            margin-bottom: 0.5rem; 
        }}
        .archetype-match {{ 
            font-size: 3.0rem; 
            font-weight: 700; 
            color: white; 
            margin: 1rem 0; 
        }}
        .archetype-description {{ 
            font-size: 1.1rem; 
            opacity: 0.95; 
            max-width: 600px; 
            margin: 0 auto; 
        }}
        .metrics-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 1rem; 
            margin-bottom: 1.5rem; 
        }}
        .metric-card {{ 
            background: white; 
            padding: 1.2rem; 
            border-radius: 8px; 
            text-align: center; 
            border: 1px solid var(--vertria-light-gray); 
            box-shadow: 0 2px 8px rgba(87, 15, 39, 0.05); 
        }}
        .metric-icon {{ 
            font-size: 2.5rem; 
            margin-bottom: 1rem; 
            color: var(--vertria-burgundy); 
        }}
        .metric-value {{ 
            font-size: 1.8rem; 
            font-weight: 700; 
            color: var(--vertria-burgundy); 
        }}
        .trait-item {{ 
            display: flex; 
            align-items: center; 
            padding: 1rem; 
            margin-bottom: 1rem; 
            background: var(--vertria-light-gray); 
            border-radius: 8px; 
            border-left: 4px solid var(--vertria-burgundy); 
        }}
        .trait-name {{ 
            flex: 1; 
            font-weight: 500; 
        }}
        .trait-score {{ 
            font-weight: 600; 
            color: var(--vertria-burgundy); 
            margin-right: 1rem; 
            min-width: 60px; 
        }}
        .trait-bar-container {{ 
            flex: 2; 
            height: 8px; 
            background: #E5E7EB; 
            border-radius: 4px; 
            overflow: hidden; 
            margin-right: 1rem; 
        }}
        .trait-bar {{ 
            height: 100%; 
            border-radius: 4px; 
        }}
        .trait-bar.low {{ 
            background: linear-gradient(90deg, #b91c1c, #ef4444); 
        }}
        .trait-bar.med {{ 
            background: linear-gradient(90deg, #f59e0b, #fbbf24); 
        }}
        .trait-bar.high {{ 
            background: linear-gradient(90deg, #15803d, #22c55e); 
        }}
        .chart-section {{ 
            margin-bottom: 1rem; 
        }}
        .chart-container {{ 
            background: white; 
            padding: 1rem; 
            border-radius: 8px; 
            box-shadow: 0 2px 8px rgba(87, 15, 39, 0.05); 
            border: 1px solid var(--vertria-light-gray); 
            margin-top: 0.5rem;
        }}
        .stage-highlight {{
            background: var(--vertria-yellow);
            color: var(--vertria-dark-blue);
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid var(--vertria-burgundy);
            margin: 1rem 0;
        }}
        .stage-chart {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 1rem 0;
            background: var(--vertria-light-gray);
            padding: 1rem;
            border-radius: 8px;
        }}
        .stage-item {{
            flex: 1;
            text-align: center;
            padding: 0.75rem;
            border-radius: 6px;
            margin: 0 0.25rem;
        }}
        .stage-item.active {{
            background: var(--vertria-burgundy);
            color: white;
        }}
        .growth-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin: 1rem 0;
        }}
        .strengths-box {{
            background: linear-gradient(135deg, var(--vertria-burgundy) 0%, var(--vertria-deep-burgundy) 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
        }}
        .growth-box {{
            background: linear-gradient(135deg, var(--vertria-yellow) 0%, #FFE888 100%);
            color: var(--vertria-dark-blue);
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid var(--vertria-burgundy);
        }}
        .reflection-questions {{
            background: var(--vertria-light-gray);
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
        }}
        .reflection-questions ol {{
            counter-reset: question-counter;
            list-style: none;
        }}
        .reflection-questions li {{
            counter-increment: question-counter;
            margin-bottom: 1.5rem;
            padding-left: 3rem;
            position: relative;
        }}
        .reflection-questions li::before {{
            content: counter(question-counter);
            position: absolute;
            left: 0;
            top: 0;
            background: var(--vertria-burgundy);
            color: white;
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
        }}
        .yellow-highlight {{
            background: var(--vertria-yellow);
            color: var(--vertria-dark-blue);
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid var(--vertria-burgundy);
            margin: 1rem 0;
        }}
        .next-steps {{
            margin: 1rem 0;
        }}
        .community-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }}
        .community-card {{
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid var(--vertria-light-gray);
            box-shadow: 0 2px 8px rgba(87, 15, 39, 0.05);
            text-align: center;
        }}
        .report-footer {{ 
            background: var(--vertria-dark-blue); 
            color: white; 
            padding: 1.5rem; 
            text-align: center; 
        }}
        /* Enhanced utility classes for professional design */
        .insight-box {{
            background: linear-gradient(135deg, var(--vertria-accent-blue) 0%, #2563EB 100%);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            margin: 1.5rem 0;
            box-shadow: var(--shadow-medium);
        }}
        
        .comparison-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
        }}
        
        .archetype-comparison-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            border: 2px solid var(--vertria-medium-gray);
            text-align: center;
            transition: all 0.3s ease;
        }}
        .archetype-comparison-card.primary {{
            border-color: var(--vertria-burgundy);
            background: linear-gradient(135deg, var(--vertria-soft-gray), white);
        }}
        
        .progress-indicator {{
            display: flex;
            align-items: center;
            margin: 0.5rem 0;
        }}
        .progress-bar {{
            flex: 1;
            height: 8px;
            background: var(--vertria-medium-gray);
            border-radius: 4px;
            margin: 0 1rem;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }}
        
        /* Enhanced component styles */
        .metrics-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); 
            gap: 1.5rem; 
            margin-bottom: 2rem; 
        }}
        .metric-card {{ 
            background: white; 
            padding: 2rem 1.5rem; 
            border-radius: 12px; 
            text-align: center; 
            border: 1px solid var(--vertria-medium-gray); 
            box-shadow: var(--shadow-medium);
            transition: all 0.3s ease;
            position: relative;
        }}
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-strong);
        }}
        .metric-card::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--vertria-burgundy), var(--vertria-yellow));
            border-radius: 12px 12px 0 0;
        }}
        
        .trait-item {{ 
            display: flex; 
            align-items: center; 
            padding: 1.5rem 1.25rem; 
            margin-bottom: 1rem; 
            background: linear-gradient(135deg, var(--vertria-soft-gray) 0%, white 100%); 
            border-radius: 12px; 
            border-left: 4px solid var(--vertria-burgundy); 
            box-shadow: var(--shadow-subtle);
            transition: all 0.3s ease;
            position: relative;
        }}
        .trait-item:hover {{
            transform: translateX(4px);
            box-shadow: var(--shadow-medium);
        }}
        
        .chart-container {{ 
            background: white; 
            padding: 2rem; 
            border-radius: 16px; 
            box-shadow: var(--shadow-medium); 
            border: 1px solid var(--vertria-medium-gray); 
            margin: 1.5rem 0;
            position: relative;
        }}
        .chart-container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--vertria-burgundy), var(--vertria-accent-blue), var(--vertria-yellow));
            border-radius: 16px 16px 0 0;
        }}
        
        .executive-summary {{ 
            background: linear-gradient(135deg, var(--vertria-soft-gray) 0%, white 100%); 
            padding: 2.5rem; 
            border-radius: 16px; 
            border-left: 6px solid var(--vertria-burgundy); 
            box-shadow: var(--shadow-medium);
            margin-bottom: 2rem;
            position: relative;
        }}
        .executive-summary::before {{
            content: '📊';
            position: absolute;
            top: 1rem;
            right: 1.5rem;
            font-size: 1.5rem;
            opacity: 0.3;
        }}
        
        .primary-archetype {{ 
            background: linear-gradient(135deg, var(--vertria-burgundy) 0%, var(--vertria-light-burgundy) 100%); 
            color: white; 
            padding: 3rem 2rem; 
            border-radius: 16px; 
            text-align: center; 
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }}
        .primary-archetype::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255, 220, 88, 0.1) 0%, transparent 70%);
            animation: float 6s ease-in-out infinite;
        }}
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
            50% {{ transform: translateY(-10px) rotate(180deg); }}
        }}
        
        .community-card {{
            background: white;
            padding: 2rem 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--vertria-medium-gray);
            box-shadow: var(--shadow-medium);
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
        }}
        .community-card:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-strong);
        }}
        .community-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 40px;
            height: 4px;
            background: var(--vertria-burgundy);
            border-radius: 0 0 4px 4px;
        }}
        
        @media (max-width: 768px) {{
            .growth-section {{ grid-template-columns: 1fr; }}
            .metrics-grid {{ grid-template-columns: 1fr; }}
            .community-grid {{ grid-template-columns: 1fr; }}
            .comparison-grid {{ grid-template-columns: 1fr; }}
            .stage-chart {{ flex-direction: column; }}
            .report-container {{ margin: 1rem; }}
            h1 {{ font-size: 2rem; }}
            h2 {{ font-size: 1.75rem; }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <!-- Header -->
        <div class="report-header">
            <div class="company-logo">VERTRIA</div>
            <h1 class="report-title">Entrepreneurial Assessment</h1>
            <div class="intro-line">You took the first step by completing the assessment. Now let us help you along your journey by detailing where you are and where you could go.</div>
            <div class="hero-quote">"{archetype_quote}"</div>
            <div class="person-name">Archetype: {archetype_name} ({archetype_score}% Match)</div>
            <div class="report-date">Generated on {datetime.now().strftime('%B %d, %Y')}</div>
        </div>
        
        <!-- Report Content -->
        <div class="report-content">
            <!-- Executive Summary -->
            <div class="section">
                <div class="executive-summary">
                    <h3>Executive Summary</h3>
                    <p>{executive_summary}</p>
                </div>
            </div>

            <!-- Primary Archetype -->
            <div class="section">
                <div class="primary-archetype">
                    <div class="archetype-name">{archetype_name}</div>
                    <div class="archetype-match">{archetype_score}%</div>
                    <div class="archetype-description">{archetype_config.ARCHETYPES[archetype.value]['description'] if archetype.value in archetype_config.ARCHETYPES else 'Strategic innovators who combine creativity with practicality to drive entrepreneurial success.'}</div>
                </div>
            </div>
            
            <!-- Assessment Metrics -->
            <div class="section">
                <h2>📊 Assessment Overview</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-icon">🎯</div>
                        <div class="metric-value">{min(sum(t.percentile for t in profile.traits) / len(profile.traits), 100):.0f}%</div>
                        <div class="metric-label">Overall Entrepreneurial Score</div>
                        <p style="font-size: 0.9rem; color: var(--vertria-text-gray); margin-top: 0.5rem;">Composite score across all traits</p>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">✅</div>
                        <div class="metric-value">{profile.completion_rate:.1%}</div>
                        <div class="metric-label">Assessment Completion</div>
                        <p style="font-size: 0.9rem; color: var(--vertria-text-gray); margin-top: 0.5rem;">Questions answered thoroughly</p>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">🔗</div>
                        <div class="metric-value">{archetype_score}%</div>
                        <div class="metric-label">Archetype Confidence</div>
                        <p style="font-size: 0.9rem; color: var(--vertria-text-gray); margin-top: 0.5rem;">Strength of archetype match</p>
                    </div>
                </div>
                
                {detailed_insights}
            </div>

            <!-- Entrepreneurial Stage -->
            <div class="section">
                <h2>Entrepreneurial Stage</h2>
                <div class="stage-highlight">
                    <h3>You are in the {stage} Stage</h3>
                    <p>{stage_description}</p>
                </div>
                
                <div class="stage-chart">
                    <div class="stage-item {'active' if stage == 'Discover' else ''}">
                        <h4>Discover</h4>
                        <p>Understanding entrepreneurial energy</p>
                    </div>
                    <div class="stage-item {'active' if stage == 'Explore' else ''}">
                        <h4>Explore</h4>
                        <p>Curious about entrepreneurship</p>
                    </div>
                    <div class="stage-item {'active' if stage == 'Build' else ''}">
                        <h4>Build</h4>
                        <p>Ready to launch ideas</p>
                    </div>
                </div>
            </div>

            <!-- Trait Analysis -->
            <div class="section">
                <h2>Trait Insights</h2>
                <div class="chart-container">
                    <h3>Interactive Trait Profile</h3>
                    <p><em>Explore your strengths and growth areas by interacting with the chart. Hover over each trait for details.</em></p>
                    <div style="margin: 1rem 0;">
                        {radar_chart_html}
                    </div>
                </div>
                
                <div class="chart-section">
                    <h3>Top 3 Traits (Archetype-based)</h3>
                    {self._generate_trait_items_continuous(top_traits, is_strength=True)}
                </div>
                
                <div class="chart-section">
                    <h3>Growth Opportunity Traits</h3>
                    {self._generate_trait_items_continuous(bottom_traits, is_strength=False)}
                </div>
            </div>

            <!-- Strengths & Growth Opportunities -->
            <div class="section">
                <h2>🚀 Strategic Development Analysis</h2>
                <div class="growth-section">
                    <div class="strengths-box">
                        <h3 style="color: var(--vertria-yellow);">✨ Core Strengths</h3>
                        <div style="margin-top: 2rem;">
                            <h4 style="color: white; margin-bottom: 1rem;">{top_traits[0].trait_name} ({top_traits[0].percentile:.0f}%)</h4>
                            <p style="margin: 1rem 0; opacity: 0.95;">Your strongest entrepreneurial asset.</p>
                            <p style="font-weight: 500;"><strong>Strategic Value:</strong> {self.trait_library.get(top_traits[0].trait_name, {}).get('importance', 'Key entrepreneurial capability.')}</p>
                            <p style="margin-top: 1rem; font-style: italic; opacity: 0.9;">"Leverage this strength to build credibility and momentum in your entrepreneurial journey."</p>
                        </div>
                    </div>
                    
                    <div class="growth-box">
                        <h3>🎯 Priority Development Area</h3>
                        <div style="margin-top: 2rem;">
                            <h4 style="margin-bottom: 1rem;">{bottom_traits[0].trait_name} ({bottom_traits[0].percentile:.0f}%)</h4>
                            <p style="margin: 1rem 0; font-weight: 500;">{self.trait_library.get(bottom_traits[0].trait_name, {}).get('definition', 'Important entrepreneurial capability')}</p>
                            <p style="margin-bottom: 1rem;"><strong>Growth Impact:</strong> {self.trait_library.get(bottom_traits[0].trait_name, {}).get('importance', 'Important area for development.')}</p>
                            <div style="background: rgba(87, 15, 39, 0.1); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                                <p style="margin: 0; font-weight: 500;">💡 Quick Win: {self.trait_library.get(bottom_traits[0].trait_name, {}).get('growth_tip', 'Focus on building this skill through regular practice and reflection.')}</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                {archetype_comparison}
            </div>

            <!-- Reflection Questions -->
            <div class="section">
                <h2>Reflection Questions</h2>
                <p style="margin-bottom: 2rem;">"Now that you've had time to digest your entrepreneurial report, it's time to start digging deeper. These reflection questions are designed to help you begin that work. At Vertria, we look forward to supporting you on the journey."</p>
                
                <div class="reflection-questions">
                    <ol>
                        {''.join(f'<li>{question}</li>' for question in reflection_questions)}
                    </ol>
                </div>
            </div>

            <!-- Community & Next Steps -->
            <div class="section">
                <h2>🚀 {next_steps_content['header']}</h2>
                
                <div class="yellow-highlight">
                    <h4>🎯 Your Entrepreneurial Journey</h4>
                    <p>{next_steps_content['growth_box']}</p>
                </div>
                
                <div class="next-steps">
                    <div class="insight-box">
                        <h3 style="color: white; margin-bottom: 1rem;">🧭 Vertria Vantage</h3>
                        <p style="color: white; opacity: 0.95;">{next_steps_content['vertria_vantage']}</p>
                    </div>
                    
                    <h3 style="margin-top: 2.5rem; margin-bottom: 1rem;">👥 Mentorship & Guidance</h3>
                    <p style="margin-bottom: 2rem;">{next_steps_content['mentors']}</p>
                    
                    <h3 style="margin-bottom: 1.5rem;">🌟 Community Ecosystem</h3>
                    <div class="community-grid">
                        <div class="community-card">
                            <div style="font-size: 2.5rem; margin-bottom: 1rem; color: var(--vertria-burgundy);">📚</div>
                            <h4 style="color: var(--vertria-burgundy);">Learning Hub</h4>
                            <p>{next_steps_content['community']['courses']}</p>
                        </div>
                        <div class="community-card">
                            <div style="font-size: 2.5rem; margin-bottom: 1rem; color: var(--vertria-accent-blue);">🎯</div>
                            <h4 style="color: var(--vertria-accent-blue);">Events & Showcases</h4>
                            <p>{next_steps_content['community']['events']}</p>
                        </div>
                        <div class="community-card">
                            <div style="font-size: 2.5rem; margin-bottom: 1rem; color: var(--vertria-success);">🤝</div>
                            <h4 style="color: var(--vertria-success);">Networking</h4>
                            <p>{next_steps_content['community']['networking']}</p>
                        </div>
                    </div>
                    
                    <div style="background: var(--vertria-soft-gray); padding: 2rem; border-radius: 12px; margin-top: 2rem; text-align: center;">
                        <h4 style="color: var(--vertria-burgundy); margin-bottom: 1rem;">Ready to Begin?</h4>
                        <p style="margin-bottom: 1.5rem;">Your entrepreneurial journey starts with a single step. Connect with Vertria today.</p>
                        <div style="display: inline-block; padding: 1rem 2rem; background: linear-gradient(135deg, var(--vertria-burgundy), var(--vertria-light-burgundy)); color: white; border-radius: 8px; font-weight: 600;">Start Your Journey →</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="report-footer">
            <p style="font-size: 1.2rem; font-style: italic; color: var(--vertria-yellow); margin-bottom: 1rem;">"The future belongs to those who act boldly."</p>
            <div style="font-size: 1.1rem; margin-bottom: 1rem;">© 2024 Vertria | info@vertria.com</div>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
    </div>
</body>
</html>"""

        # Save to file if output_path provided
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Dynamic report saved to: {output_path}")
            
        return html_content

    def _generate_trait_items_continuous(self, traits: List, is_strength: bool = True) -> str:
        """Generate HTML for trait items with proper trait bars like reference report"""
        html_items = []
        
        for trait in traits:
            trait_info = self.trait_library.get(trait.trait_name, {})
            description = trait_info.get('definition', 'Key entrepreneurial trait')
            
            # Determine bar class based on percentile
            if trait.percentile >= 70:
                bar_class = "high"
            elif trait.percentile >= 50:
                bar_class = "med"  
            else:
                bar_class = "low"
            
            bar_width = min(int(trait.percentile), 100)  # Use percentile directly
            
            html_items.append(f"""
            <div class="trait-item">
                <div class="trait-name">{trait.trait_name}</div>
                <div class="trait-score">{min(trait.percentile, 100):.0f}%</div>
                <div class="trait-bar-container">
                    <div class="trait-bar {bar_class}" style="width: {bar_width}%;"></div>
                </div>
            </div>
            """)
        
        return ''.join(html_items)

    def generate_individual_report(self, profile: PersonTraitProfile, output_dir: str = "output") -> str:
        """Generate complete individual report and return path"""
        output_path = Path(output_dir) / f"vertria_report_{profile.person_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # Create the HTML report
        self.create_html_report(profile, str(output_path))
        
        return str(output_path)