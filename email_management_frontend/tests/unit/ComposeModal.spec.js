import { mount } from '@vue/test-utils';
import { createTestingPinia } from '@pinia/testing';
import ComposeModal from '@/components/ComposeModal.vue'; // Path to the component
import { useComposeStore } from '@/stores/composeStore';
import { useEmailAccountsStore } from '@/stores/emailAccountsStore'; // Corrected path
// import { useAuthStore } from '@/stores/auth'; // Not directly used by ComposeModal from prompt

// Mock global router-link or other global components if necessary
// Vue Test Utils provides config for this in mount options.

describe('ComposeModal.vue', () => {
    let wrapper;
    let mockComposeStore;
    let mockEmailAccountsStore;
    // let mockAuthStore; // If needed

    // Reusable function to mount the component
    const mountComponent = (props = {}) => {
        const pinia = createTestingPinia({
            // createSpy: jest.fn, // If using Jest and want to spy on actions
            initialState: {
                // Provide initial state for stores if needed by the component during mount
                emailAccounts: {
                    accounts: [{ id: 1, email_address: 'test@example.com' }, {id: 2, email_address: 'another@example.com'}],
                    activeAccountId: 1, // Default active account
                },
                // compose: { ... } // Initial state for compose store if needed
            },
            stubActions: false, // Set to false if you want to test store actions being called. True by default.
                                // If true, actions are replaced by simple spies/stubs.
        });

        mockComposeStore = useComposeStore(pinia);
        mockEmailAccountsStore = useEmailAccountsStore(pinia);
        // mockAuthStore = useAuthStore(pinia);

        // Explicitly mock actions that might be called if stubActions is false or for verification
        // If stubActions is true (default), Pinia testing auto-mocks them.
        // For this test, let's assume we want to verify calls, so we might mock them ourselves or check the auto-mock.
        // If using jest.fn for createSpy with Pinia:
        mockComposeStore.sendEmail = jest.fn(() => Promise.resolve({ success: true }));
        mockComposeStore.clearStatus = jest.fn();
        // emailAccountsStore.fetchAccounts might be called onMounted if list is empty
        mockEmailAccountsStore.fetchAccounts = jest.fn(() => Promise.resolve());


        return mount(ComposeModal, {
            global: {
                plugins: [pinia],
                stubs: { // Stub child components or router-link if they cause issues
                    'router-link': true, // Simple stub for router-link
                }
            },
            props: {
                isVisible: true, // Default to visible for most tests
                initialData: null,
                ...props // Allow overriding props per test
            },
        });
    };

    beforeEach(() => {
        // Mounts before each test, or mount within each test for specific props
        // wrapper = mountComponent();
    });

    afterEach(() => {
        if (wrapper) {
            wrapper.unmount(); // Clean up component instance
        }
        jest.clearAllMocks(); // Clear all mocks
    });

    test('renders when isVisible is true', () => {
        wrapper = mountComponent({ isVisible: true });
        expect(wrapper.find('.compose-modal-content').exists()).toBe(true);
        expect(wrapper.find('h3').text()).toContain('Compose New Email');
    });

    test('does not render when isVisible is false', () => {
        wrapper = mountComponent({ isVisible: false });
        expect(wrapper.find('.compose-modal-content').exists()).toBe(false);
    });

    test('form fields exist and are correctly typed', () => {
        wrapper = mountComponent();
        expect(wrapper.find('select#fromAccount').exists()).toBe(true);
        expect(wrapper.find('input#toRecipients').exists()).toBe(true);
        expect(wrapper.find('input#ccRecipients').exists()).toBe(true);
        expect(wrapper.find('input#bccRecipients').exists()).toBe(true);
        expect(wrapper.find('input#subject').exists()).toBe(true);
        expect(wrapper.find('textarea#bodyText').exists()).toBe(true);
    });

    test('calls sendEmail action on form submit with correct data', async () => {
        wrapper = mountComponent();
        // Set form data
        const fromAccountId = 1;
        const toEmails = 'recipient@example.com, another@example.com';
        const subject = 'Test Subject';
        const body = 'Test body content';

        await wrapper.find('select#fromAccount').setValue(fromAccountId);
        await wrapper.find('input#toRecipients').setValue(toEmails);
        await wrapper.find('input#subject').setValue(subject);
        await wrapper.find('textarea#bodyText').setValue(body);

        await wrapper.find('form').trigger('submit.prevent');

        expect(mockComposeStore.sendEmail).toHaveBeenCalledTimes(1);
        expect(mockComposeStore.sendEmail).toHaveBeenCalledWith(expect.objectContaining({
            from_account_id: fromAccountId,
            to_recipients: ['recipient@example.com', 'another@example.com'],
            cc_recipients: [], // Assuming empty from input
            bcc_recipients: [], // Assuming empty from input
            subject: subject,
            body_text: body,
        }));
    });

    test('pre-fills form with initialData when provided (e.g., for reply)', async () => {
        const initialReplyData = {
            // from_account_id: 1, // Let it default or be user-selected for reply
            to_recipients: ['replyto@example.com'],
            subject: 'Re: Original Subject',
            body_text: '> Quoted text\n\nMy reply here', // Test with body_text directly
            quoted_body: '> Quoted text' // Also test fallback if body_text not set
        };
        wrapper = mountComponent({ initialData: initialReplyData });

        // Check pre-filled values
        // Note: toRecipientsStr is the v-model for the input field
        expect(wrapper.vm.toRecipientsStr).toBe('replyto@example.com'); // Check internal ref bound to input
        expect(wrapper.find('input#subject').element.value).toBe('Re: Original Subject');
        expect(wrapper.find('textarea#bodyText').element.value).toBe('> Quoted text\n\nMy reply here');
    });

    test('emits close event when cancel button is clicked', async () => {
        wrapper = mountComponent();
        // Assuming cancel button has a distinct class or data-testid, or is the first button[type=button]
        const cancelButton = wrapper.findAll('button').find(b => b.text().toLowerCase().includes('cancel'));
        expect(cancelButton.exists()).toBe(true);
        await cancelButton.trigger('click');
        expect(wrapper.emitted().close).toBeTruthy();
        expect(wrapper.emitted().close.length).toBe(1);
    });

    test('displays error message from store', async () => {
        wrapper = mountComponent();
        mockComposeStore.error = 'Failed to send: Network error'; // Simulate error in store
        await wrapper.vm.$nextTick(); // Wait for reactivity
        const errorMsgElement = wrapper.find('.error-message');
        expect(errorMsgElement.exists()).toBe(true);
        expect(errorMsgElement.text()).toContain('Failed to send: Network error');
    });

    test('displays success message from store and closes after delay', async () => {
        jest.useFakeTimers(); // Use Jest fake timers
        wrapper = mountComponent();
        mockComposeStore.sendEmail.mockImplementation(async () => {
            // Simulate successful send by setting success message in store
            mockComposeStore.successMessage = "Email sent successfully!";
            // No error
            mockComposeStore.error = null;
            return Promise.resolve({ success: true });
        });

        await wrapper.find('select#fromAccount').setValue(1);
        await wrapper.find('input#toRecipients').setValue('recipient@example.com');
        await wrapper.find('input#subject').setValue('Test Subject');
        await wrapper.find('textarea#bodyText').setValue('Test body');
        await wrapper.find('form').trigger('submit.prevent');

        await wrapper.vm.$nextTick(); // Allow store update and UI reaction

        const successMsgElement = wrapper.find('.success-message');
        expect(successMsgElement.exists()).toBe(true);
        expect(successMsgElement.text()).toContain('Email sent successfully!');

        // Fast-forward timers to check if close is emitted
        jest.advanceTimersByTime(1500); // As per setTimeout in component
        await wrapper.vm.$nextTick(); // Allow any final updates

        expect(wrapper.emitted().close).toBeTruthy();
        jest.useRealTimers(); // Restore real timers
    });

    test('fromAccount dropdown populates from emailAccountsStore and defaults correctly', async () => {
        // Initial state for emailAccountsStore is set in mountComponent
        // { accounts: [{ id: 1, email_address: 'test@example.com' }, {id: 2, email_address: 'another@example.com'}], activeAccountId: 1 }
        wrapper = mountComponent();

        const select = wrapper.find('select#fromAccount');
        const options = select.findAll('option');
        expect(options.length).toBe(2 + 0); // +1 if a "Select account" disabled option exists, 0 if not
        expect(options[0].text()).toBe('test@example.com');
        expect(options[1].text()).toBe('another@example.com');

        // Check if it defaulted to activeAccountId (1) or first account if active is not set/valid
        expect(wrapper.vm.formData.from_account_id).toBe(1); // From initial state of store
    });
});
