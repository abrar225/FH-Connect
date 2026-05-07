export async function safeCopyText(text: string) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // Browser permission can be denied in devtools, iframes, and automated browsers.
  }
  return false;
}
