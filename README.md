# Double Pendulum PyGame Sim

- Requirements:
    - `numpy`
    - `pygame`
    - `pygame-ce`
    - `pygame_gui`
    - `python-i18n`

### Demonstration 

- TODO: Insert video/gif


### Theory

To solve the system of differential equations: 
```math
\begin{align*}
    \dot\theta_1 &= \omega_1 \\
    \dot\theta_2 &= \omega_2 \\
    \dot\omega_1 &= \frac{-m_2(L_1\dot\theta_1^2\sin\Delta\theta\cos\Delta\theta + L_2\dot\theta_2^2\sin\Delta\theta)}{m_1L_1+m_2L_2\sin\Delta\theta} +
     \frac{ g( -(m_1+m_2)\sin\theta_1 + m_2\cos\Delta\theta\sin\theta_2 )}{m_1L_1+m_2L_2\sin\Delta\theta}  \\
\\
    \dot\omega_2 &= \frac{ (m_1+m_2)L_1\dot\theta_1^2\sin\Delta\theta + m_2L_2\dot\theta_2^2\sin\Delta\theta\cos\Delta\theta}{m_1L_2 + m_2L_2\sin\Delta\theta} + \frac{(m_1+m_2)g(\sin\theta_1\cos\Delta\theta - \sin\theta_2) }{m_1L_2 + m_2L_2\sin\Delta\theta}
\end{align*}
```

Consider a state vector $\mathbf Y$ where $\mathbf Y = [\theta_1,\, \theta_2,\, \omega_1,\, \omega_2]$.

Let
```math
\phi(\mathbf Y) = \begin{bmatrix}
        \omega_1 \\
        \omega_2 \\
        \alpha_1(\theta_1,\theta_2,\omega_1,\omega_2) \\
        \alpha_2(\theta_1,\theta_2,\omega_1,\omega_2)
    \end{bmatrix} 
```

Then, can write the equation in the form:
```math
\frac{\mathrm d\mathbf Y}{\mathrm dt} = \phi(\mathbf Y)
```

This can now be solved with Range-Kutta 4th Order Integration with time.
