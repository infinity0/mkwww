# Test: md

This page should look pretty much similar to the other test pages.

[rst](../topics/tech/test.html) | [adoc](../test%20with%20spaces.html)

```{contents}
```

## Link-check

Link from md [to rst](../topics/tech/test.html#_link-check)

Link from md [to adoc](../test%20with%20spaces.html#_link-check)

### Internal link check

Link to this [](Internal link check). -- TODO: currently fails due to [MyST-Parser#640](https://github.com/executablebooks/MyST-Parser/issues/640)

```{math}
---
name: Fourier transform
---
(\mathcal{F}f)(y)
 = \frac{1}{\sqrt{2\pi}^{\ n}}
   \int_{\mathbb{R}^n} f(x)\,
   e^{-\mathrm{i} y \cdot x} \,\mathrm{d} x
```

Complex math example, the [](Fourier transform).

Inline: {math}`\sqrt{a}^{b} \&`.

## Link check

test section with duplicate heading

### Test: md

test section with duplicate heading as the document title

## Very complex math

```{math}

\begin{align}
& \quad\,\, {}^{GL}_{x_0}\mathbb{D}^b_x {}^{GL}_{x_0}\mathbb{D}^a_x f(x) \\
& = \lim_{\delta \to 0} \frac{1}{\delta^b} \sum_{k=0}^{\lfloor \frac{x-x_0}{\delta} \rfloor} (-1)^k {b \choose k} {}^{GL}_{x_0}\mathbb{D}^a_x f(x-k\delta) & \text{expand ${}^{GL}_{x_0}\mathbb{D}^b_x$} \\
& = \lim_{\delta \to 0} \frac{1}{\delta^b} \sum_{k=0}^{\lfloor \frac{x-x_0}{\delta} \rfloor} (-1)^k {b \choose k} \lim_{\varepsilon \to 0} \frac{1}{\varepsilon^a} \sum_{j=0}^{\lfloor \frac{x-k\delta-x_0}{\varepsilon} \rfloor} (-1)^j {a \choose j} f(x-k\delta-j\varepsilon) & \text{expand ${}^{GL}_{x_0}\mathbb{D}^a_x$} \\
& = \lim_{\delta \to 0} \lim_{\varepsilon \to 0} \frac{1}{\delta^b} \frac{1}{\varepsilon^a} \sum_{k=0}^{\lfloor \frac{x-x_0}{\delta} \rfloor} \sum_{j=0}^{\lfloor \frac{x-k\delta-x_0}{\varepsilon} \rfloor} (-1)^k (-1)^j {b \choose k} {a \choose j} f(x-k\delta-j\varepsilon) & \text{push constants into $\lim$ and $\sum$} \\
& = \lim_{\varepsilon \to 0} \frac{1}{\varepsilon^{b+a}} \sum_{k=0}^{\lfloor \frac{x-x_0}{\varepsilon} \rfloor} \sum_{j=0}^{\lfloor \frac{x-x_0}{\varepsilon} \rfloor - k} (-1)^{k+j} {b \choose k} {a \choose j} f(x-(k+j)\varepsilon) & \text{(1), unify $\delta$ and $\varepsilon$} \\
& = \lim_{\varepsilon \to 0} \frac{1}{\varepsilon^{b+a}} \sum_{i=0}^{\lfloor \frac{x-x_0}{\varepsilon} \rfloor} \sum_{k=0}^{i} (-1)^i {b \choose k} {a \choose i-k} f(x-i\varepsilon) & \text{rearrange triangle-sum, over $i = k+j$} \\
& = \lim_{\varepsilon \to 0} \frac{1}{\varepsilon^{b+a}} \sum_{i=0}^{\lfloor \frac{x-x_0}{\varepsilon} \rfloor} (-1)^i {b+a \choose i} f(x-i\varepsilon) & \text{Vandermonde's identity} \\
& = {}^{GL}_{x_0}\mathbb{D}^{b+a}_x f(x)
\end{align}
```
