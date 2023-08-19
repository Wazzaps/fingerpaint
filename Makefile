.PHONY: all
all:
	@echo "Try one of:"
	@echo "    make update-flatpak-deps  - updates the flatpak python dependencies"
	@echo "    make flatpak-install      - installs the flatpak locally, into the user profile"
	@echo "    make flatpak              - builds the flatpak into flatpak/repo"
	@echo "    make update-flathub       - updates an adjacent 'flathub-for-fingerpaint' repo"

.PHONY: update-flatpak-deps
update-flatpak-deps:
	external/flatpak-poetry-generator.py poetry.lock -o flatpak/generated-poetry-sources.json --production

.PHONY: flatpak-install
flatpak-install:
	flatpak-builder --user --install --force-clean flatpak/build flatpak/com.github.wazzaps.Fingerpaint.yml

.PHONY: flatpak
flatpak:
	@mkdir -p flatpak/repo flatpak/build
	flatpak-builder --repo=flatpak/repo --force-clean flatpak/build flatpak/com.github.wazzaps.Fingerpaint.yml

.PHONY: update-flathub
update-flathub: flatpak/flathub-repo
	@echo "Updating flathub repo at flatpak/flathub-repo"
	@cp flatpak/com.github.wazzaps.Fingerpaint.yml flatpak/com.github.wazzaps.Fingerpaint.metainfo.xml flatpak/generated-poetry-sources.json flatpak/flathub-repo/
	@python3 flatpak/download_externals.py flatpak/flathub-repo/com.github.wazzaps.Fingerpaint.yml flatpak/flathub-repo/generated-poetry-sources.json
	@python3 flatpak/flatpak_local_to_git.py flatpak/flathub-repo/com.github.wazzaps.Fingerpaint.yml

.PHONY: clean
clean:
	rm -rf flatpak/build flatpak/repo .flatpak-builder

flatpak/flathub-repo:
	git clone --branch=new-pr git@github.com:wazzaps/flathub-for-fingerpaint.git flatpak/flathub-repo
