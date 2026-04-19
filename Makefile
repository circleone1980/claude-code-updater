.PHONY: validate test package install clean

SKILL_DIR := update-claude-code
VALIDATOR  := $(HOME)/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/scripts/quick_validate.py
SKILLS_DIR := $(HOME)/.claude/skills

validate:
	py "$(VALIDATOR)" "$(SKILL_DIR)"

test:
	py -m py_compile $(SKILL_DIR)/scripts/update.py

package: validate test
	@echo "Packaging not yet configured. Use skill-creator plugin for .skill packages."

install: validate test
	cp -r $(SKILL_DIR) $(SKILLS_DIR)/

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -f *.skill
