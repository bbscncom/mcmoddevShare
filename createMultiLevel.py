import os
import re
import sys
import shutil
import argparse
import yaml

# --- Helper Functions ---

def sanitize_name(name):
    """Sanitizes a string to be used as a directory or filename."""
    if not name:
        return ""
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>| ]+', '-', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    name = name.lower()
    if not name:
        return "untitled"
    return name

def get_heading_info(line):
    """Extracts heading level and title from a markdown line."""
    match = re.match(r'^(#+)\s*(.*)', line)
    if match:
        level = len(match.group(1))
        level = min(level, 6) # Limit level to H6
        title = match.group(2).strip()
        return level, title
    return 0, None

def read_file_with_frontmatter(filepath):
    """Reads a file, separating YAML front matter from content."""
    front_matter = {}
    content_lines = []
    in_front_matter = False
    fm_lines = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.rstrip() for line in f.readlines()]

        if lines and lines[0] == '---':
            in_front_matter = True
            lines.pop(0)

        for line in lines:
            if in_front_matter:
                if line == '---':
                    in_front_matter = False
                    try:
                        loaded_fm = yaml.safe_load('\n'.join(fm_lines))
                        front_matter = loaded_fm if loaded_fm is not None else {}
                    except yaml.YAMLError as e:
                        print(f"Warning: Could not parse front matter in {filepath}: {e}", file=sys.stderr)
                        front_matter = {}
                    continue
                fm_lines.append(line)
            else:
                content_lines.append(line)

        if in_front_matter: # Missing closing '---'
            print(f"Warning: Missing closing '---' in front matter of {filepath}. Treating as content.", file=sys.stderr)
            content_lines = fm_lines + content_lines
            front_matter = {}

    except FileNotFoundError:
        print(f"Error: File not found {filepath}", file=sys.stderr)
        return None, None
    except Exception as e:
        print(f"Error reading file {filepath}: {e}", file=sys.stderr)
        return None, None

    return front_matter, content_lines

def write_content_to_file(filepath, front_matter, content_lines):
    """Writes list of lines to a file with Front Matter, ensuring directory exists."""
    output_dir = os.path.dirname(filepath)
    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('---\n')
            yaml.dump(front_matter, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            f.write('---\n')
            if content_lines: # Only add newline if there's content
                f.write('\n')
            f.writelines(line + '\n' for line in content_lines)
    except IOError as e:
        print(f"Error saving file {filepath}: {e}", file=sys.stderr)

# --- Core Logic: Parsing and Writing ---

def parse_markdown_content_to_tree(content_lines):
    """
    Parses lines into a hierarchical node structure based on headings,
    correctly handling fenced code blocks.
    Node content stores tuples: (line_text, is_heading, original_level, original_title).
    """
    if not content_lines:
        return []

    h1_blocks_nodes = []
    current_h1_root = None
    heading_stack = [] # Stack stores node references

    # current_content_buffer stores tuples: (line_text, is_heading, heading_level, heading_title)
    current_content_buffer = []
    in_code_block = False
    code_block_fence = None # Stores the type of fence (``` or ~~~)

    # Skip content before the first actual heading or code block fence
    first_relevant_index = -1
    for i, line_text in enumerate(content_lines):
        # Check for heading or code block fence
        is_heading_line, _ = get_heading_info(line_text)
        is_fence = re.match(r'^\s*(`{3,}|~{3,})\s*(\S*)?$', line_text)
        if is_heading_line or is_fence:
            first_relevant_index = i
            break
    
    if first_relevant_index == -1: # No headings or code blocks in the file
        if content_lines: # If there was content but no structure, it's orphaned
            print(f"Warning: No H1 headings or code blocks found to structure the content. Orphaned content will be ignored.", file=sys.stderr)
        return []

    # Process relevant lines
    for line_text in content_lines[first_relevant_index:]:
        fence_match = re.match(r'^\s*(`{3,}|~{3,})\s*(\S*)?$', line_text)

        if fence_match:
            current_fence_type = fence_match.group(1)
            if not in_code_block:
                # Entering a code block
                if heading_stack: # Flush buffer to current heading before starting code block
                    heading_stack[-1]['content'].extend(current_content_buffer)
                current_content_buffer = []
                in_code_block = True
                code_block_fence = current_fence_type
                current_content_buffer.append((line_text, False, 0, None)) # Add opening fence
            elif code_block_fence and current_fence_type.startswith(code_block_fence[0]) and len(current_fence_type) >= len(code_block_fence):
                # Exiting a code block
                current_content_buffer.append((line_text, False, 0, None)) # Add closing fence
                if heading_stack: # Flush code block (including fences) to current heading
                     heading_stack[-1]['content'].extend(current_content_buffer)
                else: # Code block not under any heading (e.g., after last heading)
                    # This scenario needs careful thought. For now, assume code blocks are part of some heading's content.
                    # If a code block is truly at the end, orphaned, it might be lost if no heading_stack.
                    # This case should be rare if documents are well-structured.
                    # Let's consider if an orphaned buffer should be handled.
                    # For now, it attaches to the last known heading.
                    if current_h1_root and not heading_stack: # E.g. after all H1s are processed
                         pass # Buffer will be added to last active heading
                    elif not current_h1_root and not heading_stack:
                         print(f"Warning: Code block ending with no active heading to attach to: {line_text}", file=sys.stderr)


                current_content_buffer = []
                in_code_block = False
                code_block_fence = None
            else: # Inside a code block, and saw a fence that doesn't close it (e.g. ``` inside ~~~ block)
                 current_content_buffer.append((line_text, False, 0, None))
        elif in_code_block:
            # Line is inside a code block
            current_content_buffer.append((line_text, False, 0, None))
        else:
            # Line is not a fence and not inside a code block, check for heading
            level, title = get_heading_info(line_text)
            if level > 0: # Found a heading
                # Flush accumulated content buffer to the *previous* active heading node
                if heading_stack:
                    heading_stack[-1]['content'].extend(current_content_buffer)
                current_content_buffer = [] # Clear buffer for the new heading

                new_node = {
                    "title": title,
                    "original_level": level,
                    "content": [], # Content specific to this heading (sub-headings, text, code blocks)
                    "children": []
                }

                if level == 1:
                    current_h1_root = new_node
                    h1_blocks_nodes.append(current_h1_root)
                    heading_stack = [current_h1_root]
                else: # H2+
                    while heading_stack and heading_stack[-1]['original_level'] >= level:
                        heading_stack.pop()
                    
                    if heading_stack:
                        parent_node = heading_stack[-1]
                        parent_node['children'].append(new_node)
                        heading_stack.append(new_node)
                    elif current_h1_root: # Orphaned H2+ but there was an H1
                        print(f"Warning: Attaching H{level} '{title}' to last H1 due to structure.", file=sys.stderr)
                        current_h1_root['children'].append(new_node)
                        # Don't push to stack if parent is H1 and this is H2+, stack should be [H1, H2]
                        # This part needs review for stack management if attaching directly to H1 root
                        # For now, to ensure content capture, we'll push it temporarily.
                        # A better approach: if stack becomes empty, the new_node IS the current_h1_root's child.
                        heading_stack = [current_h1_root, new_node] if current_h1_root else [new_node]

                    else: # Orphaned H2+ and no prior H1
                        print(f"Warning: Skipping H{level} '{title}' as no parent H1 found.", file=sys.stderr)
                        # Skip this node entirely
            else: # Regular content line (not a heading, not in code block)
                current_content_buffer.append((line_text, False, 0, None))

    # After loop, flush any remaining content in the buffer to the last active heading
    if heading_stack:
        heading_stack[-1]['content'].extend(current_content_buffer)
    elif current_content_buffer: # Content at end of file not under any heading
        # This content is orphaned if no H1s were ever found or stack is empty.
        # If there was an H1 root, it could potentially be appended there.
        # However, typically content should fall under some heading.
        print(f"Warning: Content at end of file is not under any heading and will be ignored.", file=sys.stderr)


    if in_code_block:
        print("Warning: File ended unexpectedly inside a fenced code block.", file=sys.stderr)
        # The current_content_buffer for the unterminated code block would have been flushed if a heading was active.
        # If no heading was active, it might be lost here or in the above orphaned content warning.

    return h1_blocks_nodes


def write_node(node, base_output_dir, current_path_components, parent_node_title_for_nav=None, sibling_order=None, original_fm=None, is_first_h1_block=False):
    """Recursively writes a node's content and its children to files."""
    if not node:
        return

    node_original_level = node['original_level']
    node_title = node['title'] # This is already stripped by get_heading_info
    sanitized_node_name = sanitize_name(node_title)

    if not sanitized_node_name and node_original_level > 1:
        print(f"Warning: Skipping node with empty title at original level {node_original_level}: '{node_title}'", file=sys.stderr)
        return

    is_directory_node = (node_original_level == 1) or bool(node['children'])

    # --- Generate Front Matter ---
    fm = {'layout': 'default', 'title': node_title}

    if parent_node_title_for_nav:
        fm['parent'] = parent_node_title_for_nav
    
    if sibling_order is not None:
        fm['nav_order'] = sibling_order

    # Requirement 1: Add has_children: true
    if node['children']: # Check if there are actual child nodes parsed
        fm['has_children'] = True

    if is_first_h1_block and original_fm:
        original_fm_copy = original_fm.copy()
        # Use H1 title from markdown, not from original FM's title
        original_fm_copy.pop('title', None)
        
        # Preserve original nav_order if present, otherwise remove placeholder from sibling_order
        nav_order_from_original = original_fm_copy.pop('nav_order', None)

        # Merge, original_fm_copy takes precedence for non-structural keys
        temp_fm = fm.copy() # Keep generated structural keys (parent, title, potentially nav_order)
        fm = original_fm_copy # Start with original non-structural keys
        fm.update(temp_fm)   # Re-apply/override with generated structural keys

        if nav_order_from_original is not None:
            fm['nav_order'] = nav_order_from_original
        elif is_first_h1_block and 'nav_order' in fm and original_fm.get('nav_order') is None:
             # If it's the first H1, and original FM had NO nav_order,
             # but sibling_order (1) was set, remove it. Top H1 relies on _config or filename.
             if fm.get('nav_order') == 1 and sibling_order == 1 : # ensure it was from sibling_order
                  fm.pop('nav_order', None)


    # --- Generate Content Lines for the Output File ---
    output_content_lines = []
    
    # Requirement 2: Reset heading levels for the new file
    # The main heading of this new file will be H1
    # Determine if this is the very first H1 node of the original file being processed
    # (which becomes the root index.md of its own section)
    is_root_h1_of_its_section = (node_original_level == 1 and not current_path_components)

    if not is_root_h1_of_its_section:
        # For H2+ nodes becoming files, or subsequent H1 blocks from same original file
        output_content_lines.append(f"# {node_title}")
        if node['content']: # Add a blank line if there's more content
            output_content_lines.append('')
    # If it *is* the root H1 of its section, its title is already the main FM title.
    # Its content (sub-headings) will start directly.

    # Calculate level shift for headings within this node's content
    # For the root H1 of a section, its direct sub-headings (e.g. H2) should remain relative to H1 (no shift from their perspective)
    # For a node that was originally H2, its sub-headings (e.g. H3) should shift to become H2 relative to new H1.
    # Shift = target_base_level (1) - original_base_level_of_this_node
    level_shift = 1 - node_original_level

    for line_item in node['content']:
        line_text, is_line_heading, line_original_level, line_original_title = line_item
        
        if is_line_heading:
            # Requirement 3: '#' in code blocks are not headings (handled by is_line_heading flag)
            new_level = line_original_level + level_shift
            new_level = max(1, min(new_level, 6)) # Clamp between H1-H6
            output_content_lines.append(f"{'#' * new_level} {line_original_title}")
        else:
            output_content_lines.append(line_text) # Append content lines (incl. code blocks) as is

    # --- Write to File ---
    if is_directory_node:
        # Node becomes a directory with an index.md
        # Fallback for empty H1 title (e.g. "# " which sanitize_name makes "untitled")
        dir_name = sanitized_node_name if sanitized_node_name else "untitled-section"
        
        node_dir_path_components = current_path_components + [dir_name]
        output_dir_full_path = os.path.join(base_output_dir, *node_dir_path_components)
        output_filepath = os.path.join(output_dir_full_path, 'index.md')

        write_content_to_file(output_filepath, fm, output_content_lines)

        for i, child_node in enumerate(node['children']):
            write_node(child_node, base_output_dir, node_dir_path_components,
                       parent_node_title_for_nav=node_title, # Parent is current node's title
                       sibling_order=i + 1, # Children ordered 1, 2, ...
                       original_fm=None, # Original FM only for the very first H1 block
                       is_first_h1_block=False)
    else:
        # Node is a leaf page (becomes a .md file directly in parent's directory)
        # Ensure filename is not empty if title was, e.g. "## "
        leaf_filename = f"{sanitized_node_name if sanitized_node_name else 'untitled'}.md"
        output_filepath = os.path.join(base_output_dir, *current_path_components, leaf_filename)
        write_content_to_file(output_filepath, fm, output_content_lines)


def process_markdown_file(input_filepath, output_base_dir):
    """Reads a markdown file, parses, and writes to output structure."""
    print(f"Processing file: {input_filepath}")
    original_front_matter, content_lines = read_file_with_frontmatter(input_filepath)

    if content_lines is None: # Error reading file
        return

    h1_blocks_nodes = parse_markdown_content_to_tree(content_lines)

    if not h1_blocks_nodes:
        print(f"No processable H1 blocks found in {input_filepath}. Skipping.", file=sys.stderr)
        return

    for h1_block_idx, h1_node in enumerate(h1_blocks_nodes):
        is_first_h1 = (h1_block_idx == 0)
        # For multiple H1s from one file, subsequent ones are siblings
        # Their nav_order starts from 1, 2, ...
        # The very first H1 uses original FM's nav_order if present, or no nav_order.
        current_sibling_order = h1_block_idx + 1

        write_node(h1_node, output_base_dir, [],
                   parent_node_title_for_nav=None, # Top-level H1s have no FM parent
                   sibling_order=current_sibling_order,
                   original_fm=original_front_matter if is_first_h1 else None,
                   is_first_h1_block=is_first_h1)

# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Markdown files with H1-H6 hierarchy to a just-the-docs structure.")
    parser.add_argument("source_dir", nargs='?', default='.', help="Source directory with Markdown files. Defaults to current directory.")
    parser.add_argument("--output_dir", default="docs", help="Output directory for generated structure (default: docs).")
    parser.add_argument("--clean", action="store_true", help="Remove output directory before generating.")

    args = parser.parse_args()
    source_directory = args.source_dir
    output_directory = args.output_dir

    if args.clean and os.path.exists(output_directory):
        print(f"Cleaning output directory: {output_directory}")
        shutil.rmtree(output_directory)
    os.makedirs(output_directory, exist_ok=True)

    if not os.path.isdir(source_directory):
        print(f"Error: Source directory not found: {source_directory}", file=sys.stderr)
        sys.exit(1)

    try:
        markdown_files = [
            os.path.join(source_directory, f)
            for f in os.listdir(source_directory)
            if os.path.isfile(os.path.join(source_directory, f)) and f.endswith('.md')
        ]
    except Exception as e:
        print(f"Error listing files in source directory {source_directory}: {e}", file=sys.stderr)
        sys.exit(1)

    if not markdown_files:
        print(f"No .md files found in source directory: {source_directory}", file=sys.stderr)
        sys.exit(0)

    for md_file in sorted(markdown_files):
        process_markdown_file(md_file, output_directory)

    print("\nConversion complete.")
    print(f"Generated pages structure in '{output_directory}'.")
    print("Remember to configure your _config.yml for navigation and theme settings.")
