# Component System Documentation

This directory contains reusable UI components for the Karate Club Management System.

## Directory Structure

```
components/
├── cards/
│   └── stat_card.html          # Statistics card for dashboard metrics
├── forms/
│   └── form_errors.html        # Form validation error display
├── modals/
│   ├── base_modal.html         # Base modal with Alpine.js and HTMX support
│   └── confirm_modal.html      # Confirmation dialog for destructive actions
├── loading_spinner.html        # Loading spinner for HTMX requests
├── skeleton_card.html          # Skeleton loading state for cards
└── toast.html                  # Toast notification system
```

## Component Usage

### Toast Notifications

Include in base template (already included):
```html
{% include 'components/toast.html' %}
```

Show toast from JavaScript:
```javascript
showToast('Success message', 'success');
showToast('Error message', 'error');
showToast('Warning message', 'warning');
showToast('Info message', 'info');
```

### Base Modal

Include in your template:
```html
{% include 'components/modals/base_modal.html' %}
```

Open modal with Alpine.js:
```javascript
window.dispatchEvent(new CustomEvent('modal-open'));
```

Load content via HTMX:
```html
<button hx-get="/your-endpoint/" 
        hx-target="#modal-body"
        @click="$dispatch('modal-open')">
    Open Modal
</button>
```

### Confirmation Modal

Include in your template:
```html
{% include 'components/modals/confirm_modal.html' %}
```

Show confirmation:
```javascript
showConfirmModal(
    'Delete Trainee',
    'Are you sure you want to delete this trainee?',
    () => {
        // Confirmation action
        htmx.ajax('DELETE', '/trainee/123/', {target: '#trainee-list'});
    }
);
```

### Statistics Card

Include in your template:
```html
{% include 'components/cards/stat_card.html' with title="Total Trainees" value=50 icon_bg_color="bg-blue-100" icon_color="text-blue-600" link="/trainees/" %}
```

### Form Errors

Include in your form template:
```html
{% include 'components/forms/form_errors.html' %}
```

### Loading Spinner

Include inline with HTMX:
```html
<button hx-post="/endpoint/">
    Submit
    {% include 'components/loading_spinner.html' %}
</button>
```

### Skeleton Card

Show while loading:
```html
<div hx-get="/stats/" hx-trigger="load">
    {% include 'components/skeleton_card.html' %}
</div>
```

## HTMX Configuration

The base template includes:
- Automatic CSRF token injection
- Error handling with toast notifications
- Loading state management
- Success message display

## Alpine.js Components

Available Alpine.js data components:
- `toastManager()` - Toast notification management
- Modal state management with `x-data="{ open: false }"`
- Mobile menu toggle
- Notification dropdown

## Styling

All components use Tailwind CSS with custom configuration:
- Primary color: `#4F46E5` (Indigo)
- Secondary color: `#6B7280` (Gray)
- Smooth transitions and animations
- Responsive design with mobile-first approach
