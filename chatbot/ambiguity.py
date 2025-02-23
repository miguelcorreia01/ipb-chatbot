from fuzzywuzzy import fuzz
import unicodedata


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def fuzzy_match(input_str, target_str, threshold=75):
    input_no_accents = remove_accents(input_str.lower())
    target_no_accents = remove_accents(target_str.lower())
    ratio = fuzz.partial_ratio(input_no_accents, target_no_accents)
    return ratio >= threshold

def check_for_ambiguity(user_input, course_options):
    normalized_input = ' '.join(user_input.lower().split())

    exact_matches = {}
    general_terms = {}

    for general_term, degrees in course_options.items():
        for degree, courses in degrees.items():
            for course in courses:
                if course.lower() == general_term.lower():
                    if general_term not in general_terms:
                        general_terms[general_term] = {}
                    if degree not in general_terms[general_term]:
                        general_terms[general_term][degree] = []
                    general_terms[general_term][degree].append(course)
                else:
                    if general_term not in exact_matches:
                        exact_matches[general_term] = {}
                    if degree not in exact_matches[general_term]:
                        exact_matches[general_term][degree] = []
                    exact_matches[general_term][degree].append(course)

    
    for general_term, degrees in exact_matches.items():
        for degree, courses in degrees.items():
            for course in courses:
                if fuzzy_match(normalized_input, course, threshold=85):
                    return None  

    
    matched_general_terms = set()
    for general_term in list(general_terms.keys()) + list(exact_matches.keys()):
        if fuzzy_match(normalized_input, general_term, threshold=80):
            matched_general_terms.add(general_term)

    if matched_general_terms:
        available_degrees = set()
        degree_mentioned = None
        for degree in ["licenciatura", "mestrado", "ctesp"]:
            if degree in normalized_input:
                degree_mentioned = degree
                break

        for term in matched_general_terms:
            if term in general_terms:
                for degree, courses in general_terms[term].items():
                    if not degree_mentioned or degree == degree_mentioned:
                        for course in courses:
                            available_degrees.add(f"**{degree.capitalize()}** em {course}")
            
            if term in exact_matches:
                for degree, courses in exact_matches[term].items():
                    if not degree_mentioned or degree == degree_mentioned:
                        for course in courses:
                            available_degrees.add(f"**{degree.capitalize()}** em {course}")

        if degree_mentioned and len(available_degrees) == 1:
            return None 

        available_degrees_str = ", ".join(sorted(available_degrees))
        matched_terms_str = "' ou '".join(sorted(matched_general_terms))
        clarification_message = (
            f"Você mencionou algo relacionado a '{matched_terms_str}', que está disponível nos seguintes cursos e graus académicos: "
            f"{available_degrees_str}. "
            "Pode especificar qual curso e grau académico está se referindo?"
        )
        return clarification_message

    return None