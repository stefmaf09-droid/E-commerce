import emailjs from '@emailjs/browser';

/**
 * Configure these with your active EmailJS account credentials.
 * https://dashboard.emailjs.com/
 */
const EMAILJS_SERVICE_ID = 'YOUR_SERVICE_ID';
const EMAILJS_TEMPLATE_ID = 'YOUR_TEMPLATE_ID';
const EMAILJS_PUBLIC_KEY = 'YOUR_PUBLIC_KEY';

/**
 * Sends a confirmation email to the user when they finish onboarding
 * @param {string} userName
 * @param {string} companyName
 */
export const sendConfirmationEmail = async (userName, companyName) => {
  try {
    // We check if the keys are set to prevent errors during demo
    if (EMAILJS_SERVICE_ID === 'YOUR_SERVICE_ID') {
      console.warn('⚠️ EmailJS is not configured yet. Please update src/utils/email.js');
      return { success: true, dummy: true };
    }

    const templateParams = {
      to_name: userName,
      company: companyName,
      message: 'Félicitations, votre onboarding Refundly est terminé ! Nous commençons l\'analyse de vos commandes.',
    };

    const response = await emailjs.send(
      EMAILJS_SERVICE_ID,
      EMAILJS_TEMPLATE_ID,
      templateParams,
      EMAILJS_PUBLIC_KEY
    );

    console.log('Email successfully sent!', response.status, response.text);
    return { success: true, response };
  } catch (error) {
    console.error('Failed to send email:', error);
    throw error;
  }
};
