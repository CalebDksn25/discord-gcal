from rapidfuzz import fuzz

def get_best_match(query, tasks):

    final_scores = []

    for i in range(len(tasks)):
        # Extract task title from the task dictionary
        task_title = tasks[i].get("title", "")
        
        # Calculate similarity score
        score = fuzz.token_sort_ratio(query, task_title)
        print(f"DEBUG: Comparing '{query}' with '{task_title}' => Score: {score}")
        # Drop scores that are below 25
        if score >= 25:
            final_scores.append((i, score))
        else:
            continue
        
    return final_scores