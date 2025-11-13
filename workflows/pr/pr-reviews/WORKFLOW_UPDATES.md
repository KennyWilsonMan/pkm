# PR Review Workflow Updates

## Summary

Updated the automated PR review workflow to show actual code fragments from diffs instead of just line number references, with clickable links to specific lines in BitBucket.

## Changes Made

### 1. Updated `.claude/commands/review-pr-auto.md`

#### Section 3 - Fetch PR Information
- Added instructions to fetch file-specific diffs using `mode=file` parameter
- Added example showing how to get individual file diffs with actual code:
  ```
  mcp__bitbucket__bitbucket_get_pr_diff(
    mode="file",
    file_path="src/path/to/File.cs",
    context_lines=3
  )
  ```

#### Section 6 - Analyze Each Changed File
- Updated to emphasize extracting actual code changes from diff
- Added requirement to use diff data to show before/after code
- Added instruction to link to specific line numbers in BitBucket

#### Section 9 - Generate Complete Review Report
- Updated file review template to show actual code diffs
- Added format showing `diff` code blocks with +/- lines
- Added example showing before/after code changes
- Added links to specific line numbers in BitBucket format: `{pr-url}#path/to/file.ext-{line-number}`

**New Format Example:**
```markdown
### 📄 `src/Service.cs`

#### Changes Made

**Line 52-59: Changed from `.Result` to `.GetAwaiter().GetResult()`**

```diff
  var httpClient = httpClientFactory.CreateClient("AuthService");
  try
  {
-     var response = httpClient.GetAsync(authEndpointUrl).Result;
+     var response = httpClient.GetAsync(authEndpointUrl).GetAwaiter().GetResult();
      if (response.StatusCode != HttpStatusCode.OK)
      {
          logger.LogError("Error: {StatusCode}", response.StatusCode);
          return;
      }
```

Explanation of the change and its impact...

**[View this change in BitBucket]({pr-url}#src/Service.cs-52)**
```

### 2. Enhanced `convert_to_html.py`

#### Diff Syntax Highlighting
- Added special handling for `diff` code blocks
- Lines starting with `+` (additions) are highlighted in green background (#e6ffec)
- Lines starting with `-` (removals) are highlighted in red background (#ffebe9)
- Lines starting with `@@` (hunk headers) are shown in blue
- Unchanged context lines have no special highlighting

#### Updated CSS Styles
- Improved code block styling with better fonts
- Added specific styles for diff blocks
- Better line spacing and padding for readability

## Benefits

1. **More Informative Reviews**: Reviewers can see the actual code changes without navigating to BitBucket
2. **Better Context**: Shows surrounding code context to understand the change location
3. **Direct Navigation**: Links allow quick jump to specific changes in BitBucket
4. **Visual Clarity**: HTML version renders diffs with color coding (green for additions, red for removals)
5. **Self-Contained**: Review documents include all necessary information

## Usage

The next time you run `/review-pr-auto <pr-url>`, the review will automatically:

1. Fetch individual file diffs for each changed file
2. Extract the actual code changes with +/- indicators
3. Include the code fragments in the review with explanations
4. Generate clickable links to specific line numbers in BitBucket
5. Convert to HTML with syntax-highlighted diffs

## Example Output

### Markdown
```markdown
**Line 15-18: Changed internal collections from List to HashSet**

```diff
- private readonly List<string> _audiences = new List<string>();
- private readonly List<string> _issuers = new List<string>();
+ private readonly HashSet<string> _audiences = new HashSet<string>();
+ private readonly HashSet<string> _issuers = new HashSet<string>();
```

This improves performance from O(n) to O(1) for Contains operations.

**[View this change in BitBucket](https://mangit.../pull-requests/134#src/AuthenticationService.cs-15)**
```

### HTML Rendered
The HTML version will show:
- Red-highlighted lines for removals
- Green-highlighted lines for additions
- Monospace font for code
- Clickable link to BitBucket

## Files Modified

1. `/turbo/kewilson/github/pkm/workflows/pr/.claude/commands/review-pr-auto.md`
   - Updated sections 3, 6, and 9
   - Added detailed instructions and examples

2. `/turbo/kewilson/github/pkm/workflows/pr/pr-reviews/convert_to_html.py`
   - Enhanced diff code block handling
   - Added color-coded syntax highlighting
   - Improved CSS styling

## Testing

To test the new workflow:

1. Run: `/review-pr-auto <pr-url>`
2. Check the generated markdown for actual code diffs
3. Open the HTML version to see color-coded changes
4. Click BitBucket links to verify they navigate to correct lines

## Notes

- The workflow now requires fetching individual file diffs, which may take slightly longer
- BitBucket line number links use the format: `#filepath-linenumber`
- Diff blocks show 3 lines of context by default (configurable with `context_lines` parameter)
- HTML conversion properly handles diff syntax with green/red highlighting
