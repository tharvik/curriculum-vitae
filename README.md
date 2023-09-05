# How to build

You would need

- `>=dev-lang/python-3.11`
- `dev-python/pip`

For optional pdf generation with libreoffice backend

- `app-office/libreoffice || app-office/libreoffice-bin`: https://www.libreoffice.org
- `app-text/poppler`: https://poppler.freedesktop.org/
  - for cleaning empty pages generated by libreoffice

For optional pdf generation with pandoc backend

- `app-text/pandoc-cli`: https://pandoc.org
  - Gentoo users, you can find it in the haskell overlay

Then you can install it with

```python
pip install .
```

And use it with your config

```python
cv odt < config.toml > cv.odt
```

Or with you preferred viewer

```python
cv pdf < config.toml | zathura -
```
