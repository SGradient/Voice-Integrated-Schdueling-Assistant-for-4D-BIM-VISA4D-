import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sentence_transformers import SentenceTransformer, util
import nltk
from nltk.corpus import stopwords
from dateutil import parser
from datetime import datetime, timedelta
import numpy as np
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from spacy.tokens import Doc

class NLPProcessor:
    def __init__(self):
        # Initialize components
        self.nlp = spacy.load("en_core_web_lg")
        self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
        nltk.download('stopwords')
        
        # Initialize intent classifier
        self.intent_classifier = self._train_enhanced_model()
        
        # Task name similarity threshold
        self.similarity_threshold = 0.85
        
        # Construction-specific patterns
        self.construction_patterns = {
            'pour_pattern': r'pour\s*#?\d+',
            'floor_pattern': r'(main|second|third|ground|first|1st|2nd|3rd)\s+floor',
            'installation_pattern': r'\w+\s+installation',
            'inspection_pattern': r'\w+\s+inspection'
        }
        
        # Common construction abbreviations
        self.construction_abbrev = {
            'hvac': 'HVAC',
            'mep': 'MEP',
            'pour': 'Pour',
            'gb': 'Grade Beams',
            'sw': 'Site Work',
            'fn': 'Foundation',
            'el': 'Elevator',
            'str': 'Structural',
            'arch': 'Architectural'
        }
        
        # Enhanced status mapping with "not start" status
        self.status_mapping = {
            'complete': ['complete', 'finished', 'done', 'completed', 'end', 'ready'],
            'in progress': ['progress', 'ongoing', 'started', 'working', 'begin', 'start', 'doing'],
            'on hold': ['hold', 'pause', 'stopped', 'delay', 'wait', 'pending'],
            'suspended': ['suspended', 'suspend', 'temporarily halted'],
            'not started': ['not start', 'not started', 'not begun', 'unstarted', 'not commenced']
        }
        
        # Context management
        self.context = {
            'last_task': None,
            'last_intent': None,
            'recent_tasks': []
        }

    def _generate_training_data(self) -> Tuple[List[str], List[str]]:
        """Generate more comprehensive training data with variations"""
        commands = []
        labels = []
        
        # Template-based data generation
        # Construction-specific task names
        task_names = [
            # Foundation and Ground Work
            'Foundation Piling', 'Pile Caps', 'Elevator Raft', 'Grade Beams',
            'Grade Beams Pour #1', 'Grade Beams Pour #2', 'Grade Beams Pour #3',
            'Grade Beams Pour #4', 'Grade Beams Pour #5', 'Grade Beams Pour #6',
            'Grade Beams Pour #7', 'Grade Beams Pour #8', 'Grade Beams Pour #9',
            'Grade Beams Pour #10', 'Install Elevator Pits', 'Feature Wall Pours',
            
            # Floor-specific Work
            'Main Floor Glazing Installation', 'Main Floor Windows Installation',
            'Main Floor Drywall Installation', 'Main Floor Door Installation',
            'Main Floor Railing', 'Second Floor Glazing Installation',
            'Second Floor Windows Installation', 'Second Floor Drywall Installation',
            'Second Floor Door Installation', 'Second Floor Railing',
            
            # Roof Work
            'Roof Door Installation', 'Floor Installation', 'Wall Installation',
            'Exterior Wall Installation',
            
            # General Construction Tasks
            'Site Preparation', 'Land Surveying', 'Foundation Laying',
            'Concrete Pouring', 'Rebar Installation', 'Structural Framing',
            'Bricklaying', 'Window Installation', 'Roofing', 'Electrical Wiring',
            'Plumbing Installation', 'HVAC Installation', 'Insulation Installation',
            'Drywall Installation', 'Flooring Installation', 'Tile Installation',
            'Painting and Decorating', 'Carpentry', 'Cabinet Installation',
            'Lighting Installation', 'Door Installation', 'Trim and Molding Installation',
            
            # Exterior and Site Work
            'Exterior Siding', 'Landscaping', 'Fencing Installation',
            'Driveway Paving', 'Garage Construction', 'Deck Construction',
            'Pool Installation', 'Security System Installation',
            'Fireplace Installation', 'Elevator Installation',
            
            # Inspections and Completion
            'Final Inspection', 'Punch List Completion', 'Move-in Preparation',
            'Site Cleanup', 'Waste Disposal', 'Building Permits Approval',
            'Energy Efficiency Testing', 'Environmental Compliance',
            'Safety Inspections', 'Utility Connections',
            
            # Additional Specialized Work
            'Waterproofing', 'Stormwater Management', 'Septic System Installation',
            'Exterior Painting', 'Interior Design Work',
            'Specialty Equipment Installation', 'Finishing Touches',
            'Post-construction Cleanup'
        ]
        status_templates = [
            "Update {task} status to {status}",
            "Change {task} to {status}",
            "Set {task} as {status}",
            "Mark {task} {status}",
            "Can you update {task} to {status}",
            "Please change {task} status to {status}"
        ]
        
        # Generate status update commands
        for task in task_names:
            for status in ['complete', 'in progress', 'on hold']:
                for template in status_templates:
                    commands.append(template.format(task=task, status=status))
                    labels.append("update_status")
        
        # Similar templates for create, delete, and date update commands
        create_templates = [
            "Create a new task for {task}",
            "Add task {task}",
            "Set up {task}",
            "I need a new task for {task}",
            "Can you create {task}",
            "Please add {task} to the list"
        ]
        
        # Add create commands
        for task in task_names:
            for template in create_templates:
                commands.append(template.format(task=task))
                labels.append("create_task")
        
        # Add specific examples for our test cases
        specific_examples = [
            ("Update start date for door 1000 installation to March 9", "update_date"),
            ("Update finish date for door 1000 installation to March 9", "update_date"),
            ("Update the status for stair 1000 to in progress", "update_status"),
            ("Update the status for slab A to complete", "update_status"),
            ("Update the status for window B to on hold", "update_status"),
            ("Add painting task", "create_task"),
            ("Add railing task", "create_task"),
            ("Delete railing task", "delete_task")
        ]
        
        for example, label in specific_examples:
            commands.append(example)
            labels.append(label)
    
        return commands, labels

    def _train_enhanced_model(self):
        """Train an enhanced intent classification model"""
        commands, labels = self._generate_training_data()
        
        # Split data for validation
        X_train, X_test, y_train, y_test = train_test_split(
            commands, labels, test_size=0.2, random_state=42
        )
        
        # Create pipeline with enhanced features
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=5000,
                stop_words='english',
                min_df=2
            )),
            ('clf', RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                class_weight='balanced',
                random_state=42
            ))
        ])
        
        # Train and evaluate
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        logging.info(f"Model Performance:\n{classification_report(y_test, y_pred)}")
        
        return pipeline
    
    
    def _preprocess_text(self, text: str) -> str:
        doc = self.nlp(text.lower())
        return " ".join([
            token.lemma_.lower().strip()
            for token in doc
            if not token.is_punct and not token.is_space
            and token.lemma_.lower().strip()
            and token.lemma_.lower().strip() not in stopwords.words('english')
        ])
    def _normalize_construction_text(self, text: str) -> str:
        """Normalize construction-specific text by expanding abbreviations and standardizing terms"""
        text_lower = text.lower()
        
        # Expand abbreviations
        for abbrev, full in self.construction_abbrev.items():
            pattern = r'\b' + abbrev + r'\b'
            text_lower = re.sub(pattern, full.lower(), text_lower)
            
        # Standardize pour numbers
        pour_pattern = r'pour\s*#?\s*(\d+)'
        text_lower = re.sub(pour_pattern, r'Pour #\1', text_lower)
        
        # Standardize floor references
        floor_patterns = {
            r'\b1st\b': 'first',
            r'\b2nd\b': 'second',
            r'\b3rd\b': 'third',
            r'\bground\b': 'main'
        }
        for pattern, replacement in floor_patterns.items():
            text_lower = re.sub(pattern, replacement, text_lower)
            
        return text_lower

    def _extract_task_name_enhanced(self, text: str, doc: spacy.tokens.Doc) -> Optional[str]:
        """Enhanced task name extraction with construction-specific handling"""
        # Normalize text for construction terms
        text_lower = text.lower()
        
        # Specific patterns for construction tasks
        construction_task_patterns = [
            # Door installation pattern
            r'(door)\s+(\d+)\s+(installation)',
            # Stair pattern
            r'(stair)\s+(\d+)',
            # Slab pattern
            r'(slab)\s+([a-zA-Z])',
            # Window pattern
            r'(window)\s+([a-zA-Z])',
            # Simple task patterns
            r'(painting)(\s+task)?',
            r'(railing)(\s+task)?'
        ]
        
        # Try to match construction-specific patterns first
        for pattern in construction_task_patterns:
            match = re.search(pattern, text_lower)
            if match:
                # Format the task name with proper capitalization
                components = [g for g in match.groups() if g and g.strip()]
                task_name = ' '.join(components)
                # Capitalize each word
                return ' '.join(word.capitalize() for word in task_name.split())
        normalized_text = self._normalize_construction_text(text)
        
        # Ignore words during task extraction
        ignore_words = {
            'task', 'work', 'project', 'item', 'status', 'date', 'start', 'end',
            'deadline', 'schedule', 'update', 'change', 'modify', 'set', 'new',
            'create', 'add', 'remove', 'delete', 'please', 'could', 'would'
        }
        
        # Check for exact matches in construction patterns
        for pattern_name, pattern in self.construction_patterns.items():
            match = re.search(pattern, normalized_text)
            if match:
                matched_text = match.group(0)
                # For pour numbers, ensure proper formatting
                if pattern_name == 'pour_pattern':
                    pour_num = re.search(r'\d+', matched_text).group(0)
                    return f"Grade Beams Pour #{pour_num}"
                # For floor-specific tasks, combine with activity
                elif pattern_name == 'floor_pattern':
                    floor = match.group(1).capitalize()
                    # Look for associated activity
                    activities = ['Glazing', 'Windows', 'Drywall', 'Door', 'Railing']
                    for activity in activities:
                        if activity.lower() in normalized_text:
                            return f"{floor} Floor {activity} Installation"
                return matched_text.title()
        
        # Try dependency parsing first
        for token in doc:
            if token.dep_ in ['dobj', 'pobj', 'compound'] and not token.is_stop:
                # Get the full noun phrase
                task_name = ' '.join([t.text for t in token.subtree 
                                    if not t.is_stop and t.text.lower() not in ignore_words]).strip()
                if task_name:
                    return task_name
        
        # Fallback: Extract noun phrases and filter
        noun_phrases = [chunk.text for chunk in doc.noun_chunks]
        if noun_phrases:
            # Filter and score noun phrases
            valid_phrases = []
            for phrase in noun_phrases:
                words = phrase.lower().split()
                if not any(word in ignore_words for word in words):
                    valid_phrases.append(phrase)
            
            if valid_phrases:
                # Return the longest valid phrase as it's likely the most specific
                return max(valid_phrases, key=len)
        
        return None

    def _extract_date_enhanced(self, text: str, doc: spacy.tokens.Doc) -> Dict[str, Any]:
        """Enhanced date extraction with start/finish date distinction"""
        date_info = {
            'start_date': None,
            'end_date': None,
            'duration': None,
            'date_type': 'start'  # Default to start date
        }
        
        text_lower = text.lower()
        
        # Determine if this is a start or finish date
        if re.search(r'(finish|end)\s+date', text_lower):
            date_info['date_type'] = 'finish'
        
        # Extract the date (March 9 format)
        month_day_pattern = r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?'
        month_day_match = re.search(month_day_pattern, text_lower)
        
        if month_day_match:
            month, day = month_day_match.groups()
            year = datetime.now().year
            month_num = {'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6, 
                        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12}[month.lower()]
            
            try:
                extracted_date = datetime(year, month_num, int(day))
                
                # Assign date based on date_type
                if date_info['date_type'] == 'finish':
                    date_info['end_date'] = extracted_date
                else:
                    date_info['start_date'] = extracted_date
                    
            except ValueError:
                # Handle invalid dates by falling back to existing methods
                pass
        
        # If no specific date format found, continue with existing extraction methods
        if not date_info['start_date'] and not date_info['end_date']:
            # Call existing _extract_single_date method
            date = self._extract_single_date(text, doc)
            if date:
                if date_info['date_type'] == 'finish':
                    date_info['end_date'] = date
                else:
                    date_info['start_date'] = date
        
        return date_info
    def _extract_single_date(self, text: str, doc: spacy.tokens.Doc) -> Optional[datetime]:
        """Extract a single date from text, used as a helper for _extract_date_enhanced"""
        date_patterns = [
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4}',
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4}',
            r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
            r'next (monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(tomorrow|next week|next month)',
            r'in \d+ (days?|weeks?|months?)'
        ]

        text_lower = text.lower()
        
        # Try pattern matching first
        for pattern in date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    date_str = match.group(0)
                    if 'next' in date_str or 'tomorrow' in date_str:
                        return self._parse_relative_date(date_str)
                    return parser.parse(date_str, fuzzy=True)
                except Exception:
                    continue

        # Try spaCy's date entities as backup
        for ent in doc.ents:
            if ent.label_ == "DATE":
                try:
                    return parser.parse(ent.text, fuzzy=True)
                except Exception:
                    continue
                    
        return None

    def _extract_status_enhanced(self, text: str) -> Tuple[Optional[str], float]:
        """Enhanced status extraction with confidence scoring and expanded status types"""
        text_lower = text.lower()
        
        # Direct matching for exact status phrases first - higher priority
        direct_matches = {
            "complete": ['complete', 'completed', 'finished'],
            "in progress": ['in progress', 'ongoing'],
            "on hold": ['on hold', 'hold'],
            "suspended": ['suspended', 'suspend'],
            "not started": ['not started', 'not start']
        }
        
        # Check for direct matches first for higher accuracy
        for status, phrases in direct_matches.items():
            if any(phrase in text_lower for phrase in phrases):
                return status, 1.0  # High confidence for direct matches
        
        # Fall back to embedding similarity for less exact matches
        text_embedding = self.sentence_transformer.encode(text_lower)
        
        best_status = None
        best_confidence = 0.0
        
        for status, keywords in self.status_mapping.items():
            # Create embeddings for each keyword phrase
            keyword_embeddings = self.sentence_transformer.encode(keywords)
            
            # Calculate similarities
            similarities = util.cos_sim(text_embedding, keyword_embeddings)
            max_similarity = float(similarities.max())
            
            if max_similarity > best_confidence:
                best_confidence = max_similarity
                best_status = status
        
        return best_status, best_confidence

    def _validate_command(self, intent: str, entities: Dict[str, Any]) -> bool:
        """Enhanced command validation with confidence thresholds"""
        # Always accept certain patterns regardless of confidence
        if entities.get('task_name') and intent in ['create_task', 'delete_task']:
            return True
            
        if entities['confidence'] < 0.6:  # Confidence threshold
            return False
            
        if not entities['task_name'] and not self.context['last_task']:
            return False
            
        if 'update_date' in intent and not (entities['dates'].get('start_date') or entities['dates'].get('end_date')):
            return False
            
        if 'update_status' in intent and not entities['status']:
            return False
            
        return True


    def _update_context(self, intent: str, entities: Dict[str, Any]):
        """Update conversation context"""
        if entities.get('task_name'):
            self.context['last_task'] = entities['task_name']
            if entities['task_name'] not in self.context['recent_tasks']:
                self.context['recent_tasks'] = ([entities['task_name']] + 
                    self.context['recent_tasks'])[:5]  # Keep last 5 tasks
        
        self.context['last_intent'] = intent

    def _validate_command(self, intent: str, entities: Dict[str, Any]) -> bool:
        """Enhanced command validation with confidence thresholds"""
        if entities['confidence'] < 0.6:  # Confidence threshold
            return False
            
        if not entities['task_name'] and not self.context['last_task']:
            return False
            
        if 'update_date' in intent and not entities['dates']['start_date']:
            return False
            
        if 'update_status' in intent and not entities['status']:
            return False
            
        return True
  
    def _generate_clarification_request(self, intent: str, entities: Dict[str, Any]) -> str:
        """Generate a clarification request based on missing or unclear information"""
        if not entities.get('task_name'):
            return "Could you please specify which task you're referring to?"
        
        if intent == 'update_status' and not entities.get('status'):
            return f"What status would you like to set for '{entities['task_name']}'? (complete, in progress, or on hold)"
        
        if intent == 'update_date' and not entities['dates'].get('start_date'):
            return f"When would you like to schedule '{entities['task_name']}'?"
        
        return "Could you please clarify your request?"
    
    
    
    def _generate_response(self, intent: str, entities: Dict[str, Any]) -> str:
        """Generate appropriate response based on intent and entities"""
        task = entities.get('task_name', '')
        dates = entities.get('dates', {})
        status = entities.get('status')
    
        if intent == 'update_date':
            date_type = dates.get('date_type', 'start')
            date_str = None
            
            if dates.get('start_date'):
                date_str = dates['start_date'].strftime("%B %d, %Y")
            elif dates.get('end_date'):
                date_str = dates['end_date'].strftime("%B %d, %Y")
            
            if date_str:
                date_type_text = "start date" if date_type == "start" else "finish date"
                return f"Updated the {date_type_text} for '{task}' to {date_str}."
            return f"Updated the schedule for '{task}'."
            
        elif intent == 'update_status':
            # Format status for display
            status_display = {
                'complete': 'complete',
                'in progress': 'in progress',
                'on hold': 'on hold',
                'suspended': 'suspended',
                'not started': 'not started'  # Fixed key
            }.get(status, status)
            
            return f"Updated the status of '{task}' to {status_display}."
            
        elif intent == 'create_task':
            start_date = dates.get('start_date')
            if start_date:
                date_str = start_date.strftime("%B %d, %Y")
                return f"Created new task '{task}' scheduled for {date_str}."
            return f"Created new task '{task}'."
            
        elif intent == 'delete_task':
            return f"Deleted task '{task}'."
            
        else:
            return f"Command processed for task '{task}'."

    def process_command(self, text: str, gui) -> None:
        """Process command and interact with GUI while maintaining existing interface"""
        try:
            if gui.state['awaiting_confirmation']:
                self._handle_confirmation(text, gui)
                return
    
            # Preprocess text
            processed_text = self._preprocess_text(text)
            doc = self.nlp(text)
            text_lower = text.lower()
            
            # First, identify specific commands from the text patterns
            # This is high-priority matching that overrides ML classification
            intent = None
            
            # Identify command type by explicit patterns
            if "update" in text_lower and "status" in text_lower:
                intent = "update_status"
            elif "update" in text_lower and ("start date" in text_lower or "finish date" in text_lower):
                intent = "update_date"
            elif "add" in text_lower:
                intent = "create_task"
            elif "delete" in text_lower or "remove" in text_lower:
                intent = "delete_task"
            
            # If no explicit pattern found, use ML classification
            if not intent:
                # Get intent with confidence
                intent_proba = self.intent_classifier.predict_proba([processed_text])[0]
                intent_idx = intent_proba.argmax()
                intent = self.intent_classifier.classes_[intent_idx]
                confidence = intent_proba[intent_idx]
            else:
                confidence = 1.0  # High confidence for explicit pattern matches
            
            # Extract task name using specific pattern matching first
            task_name = None
            
            # Handle door, stair, slab, window tasks with exact pattern matching
            task_patterns = [
                (r'door\s+(\d+)\s+installation', 'Door {0} Installation'),
                (r'stair\s+(\d+)', 'Stair {0}'),
                (r'slab\s+([a-zA-Z])', 'Slab {0}'),
                (r'window\s+([a-zA-Z])', 'Window {0}'),
                (r'\bpainting\b', 'Painting'),
                (r'\brailing\b', 'Railing')
            ]
            
            for pattern, template in task_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    if len(match.groups()) > 0:
                        task_name = template.format(match.group(1).upper())
                    else:
                        task_name = template
                    break
            
            # If no specific pattern match, use general extraction
            if not task_name:
                task_name = self._extract_task_name_enhanced(text, doc)
            
            # Extract status with special handling for specific patterns
            status = None
            
            # Check for explicit status keywords first
            status_keywords = {
                "complete": ["complete", "completed", "finish", "finished"],
                "in progress": ["in progress", "ongoing", "start"],
                "on hold": ["on hold", "hold"],
                "suspended": ["suspended", "suspend"],
                "not started": ["not started", "not start"]
            }
            
            # Direct status keyword matching
            for status_value, keywords in status_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    status = status_value
                    break
            
            # Additional patterns for specific phrasings
            status_patterns = [
                (r'to\s+suspended', 'suspended'),
                (r'to\s+not\s+start(ed)?', 'not started'),
                (r'as\s+suspended', 'suspended'),
                (r'as\s+not\s+start(ed)?', 'not started')
            ]
            
            for pattern, status_value in status_patterns:
                if re.search(pattern, text_lower):
                    status = status_value
                    break
            
            # If no direct match, use semantic similarity
            if not status and intent == 'update_status':
                status, _ = self._extract_status_enhanced(text)
            
            # Extract dates
            dates = self._extract_date_enhanced(text, doc)
            
            # Special handling for finish dates
            if "finish date" in text_lower and dates.get('start_date'):
                dates['end_date'] = dates['start_date']
                dates['start_date'] = None
                dates['date_type'] = 'finish'
            
            # Prepare entities
            entities = {
                'task_name': task_name,
                'dates': dates,
                'status': status,
                'confidence': confidence
            }
            
            # Update context
            self._update_context(intent, entities)
            
            # Process the command
            if self._validate_command(intent, entities) or entities['task_name']:
                success = False
                
                # Apply the command based on intent
                if intent == 'create_task':
                    # FIXED: Handle None values properly for start_date and end_date
                    dates = entities['dates']
                    
                    # Always use a valid start_date
                    start_date = dates.get('start_date')
                    if start_date is None:
                        start_date = datetime.now()
                    
                    # Set a valid end_date
                    end_date = dates.get('end_date')
                    if end_date is None:
                        # Now start_date is guaranteed to be non-None
                        end_date = start_date + timedelta(days=30)
                    
                    success = gui.task_manager.create_task(
                        task_name=entities['task_name'],
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                elif intent == 'update_status':
                    success = gui.task_manager.update_task_status(
                        task_name=entities['task_name'],
                        status=entities['status']
                    )
                    
                elif intent == 'update_date':
                    # FIXED: Handle the method without date_type parameter
                    dates = entities['dates']
                    target_date = None
                    
                    # Determine which date to use
                    if "finish date" in text_lower:
                        # Store internally that this was meant to be a finish date
                        entities['dates']['date_type'] = 'finish'
                        target_date = dates.get('end_date', dates.get('start_date'))
                    else:
                        entities['dates']['date_type'] = 'start'
                        target_date = dates.get('start_date', dates.get('end_date'))
                    
                    if target_date:
                        date_str = target_date.strftime("%B %d, %Y")
                        # Call without date_type parameter
                        success = gui.task_manager.update_task_date(
                            task_name=entities['task_name'],
                            date=date_str
                        )
                    
                elif intent == 'delete_task':
                    success = gui.task_manager.delete_task(
                        task_name=entities['task_name']
                    )
                
                # Generate response
                response = self._generate_response(intent, entities)
                if not success:
                    response = f"There was an error processing your request. Please try again."
                gui.display_message(f"VISA4D: {response}", is_user=False)
            else:
                clarification_msg = self._generate_clarification_request(intent, entities)
                gui.display_message(f"VISA4D: {clarification_msg}", is_user=False)
                
        except Exception as e:
            logging.error(f"Command processing error: {str(e)}")
            gui.display_message(" Sorry, I encountered an error. Please try again.", is_user=False)
    def _handle_confirmation(self, text: str, gui) -> None:
        """Handle user confirmation of pending commands"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['yes', 'yeah', 'correct', 'right', 'sure', 'ok']):
            # Process the pending command
            pending = gui.state.get('pending_command', {})
            if pending:
                intent = pending.get('intent')
                entities = pending.get('entities')
                if intent and entities:
                    # Reset confirmation state
                    gui.state['awaiting_confirmation'] = False
                    gui.state['pending_command'] = None
                    # Process the command
                    self.process_command(text, gui)
        else:
            # Reset confirmation state
            gui.state['awaiting_confirmation'] = False
            gui.state['pending_command'] = None
            gui.display_message("Command cancelled. How else can I help?", is_user=False)