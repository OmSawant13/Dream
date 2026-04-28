import logging

logger = logging.getLogger("papper-observer")

class BrowserObserver:
    """Phase B: The Grid. PRO-GRADE Perception with Dict-based Dedup."""
    def __init__(self, controller):
        self.controller = controller
        self.element_map = {}

    async def capture_grid(self):
        """Capture page state with efficient dedup and human-centric sorting."""
        try:
            page = await self.controller.get_active_page()
            
            # THE PROBE: Shadow DOM + Parent-Child Dedup + Visual Sorting
            elements = await page.evaluate("""() => {
                const results = [];
                const INTERACTIVE_TAGS = ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'];
                const INTERACTIVE_ROLES = ['button', 'link', 'textbox', 'checkbox', 'menuitem', 'tab', 'combobox'];

                function getVisibleElements(container) {
                    const all = container.querySelectorAll('*');
                    all.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        
                        const isVisible = rect.width > 2 && rect.height > 2 && 
                                          style.visibility !== 'hidden' && 
                                          style.display !== 'none' &&
                                          style.opacity !== '0';

                        if (isVisible) {
                            const role = el.getAttribute('role');
                            const name = el.innerText?.trim() || el.getAttribute('aria-label') || 
                                         el.getAttribute('title') || el.placeholder || el.value;
                            
                            const isTag = INTERACTIVE_TAGS.includes(el.tagName);
                            const isRole = INTERACTIVE_ROLES.includes(role);
                            const hasPointer = style.cursor === 'pointer';
                            
                            if ((isTag || isRole || hasPointer) && name && name.length > 0) {
                                results.push({
                                    role: role || el.tagName.toLowerCase(),
                                    name: name.substring(0, 60).replace(/\\n/g, ' ').trim(),
                                    x: rect.left + rect.width / 2,
                                    y: rect.top + rect.height / 2,
                                    area: rect.width * rect.height
                                });
                            }
                        }

                        if (el.shadowRoot) {
                            getVisibleElements(el.shadowRoot);
                        }
                    });
                }

                getVisibleElements(document);

                // FIX #2: Row banding increased to 60px to better handle modern UI heights
                results.sort((a, b) => {
                    const rowA = Math.floor(a.y / 60);
                    const rowB = Math.floor(b.y / 60);
                    if (rowA !== rowB) return rowA - rowB;
                    return a.x - b.x;
                });

                return results;
            }""")
            
            self.element_map = {}
            index = 0
            view = f"\n--- CURRENT VIEW: {page.url} ---\n"
            
            # FIX #1: Dict-based O(N) deduplication (Performance improvement)
            ded_map = {} # Map coord_key -> smallest_element
            for el in elements:
                coord_key = f"{round(el['x'])},{round(el['y'])}"
                # Smallest area at a specific point wins (usually the specific button inside a div)
                if coord_key not in ded_map or el['area'] < ded_map[coord_key]['area']:
                    ded_map[coord_key] = el

            # Final Grid Generation
            for el in ded_map.values():
                if index >= 200: break
                self.element_map[str(index)] = el
                view += f"[{index}] {el['role'].upper()}: \"{el['name']}\"\n"
                index += 1
            
            if index == 0:
                view += "(No interactive elements found.)"
                
            return view
        except Exception as e:
            logger.error(f"Perception Error: {e}")
            return f"❌ Perception Error: {e}"

    def get_element(self, index):
        return self.element_map.get(str(index))
