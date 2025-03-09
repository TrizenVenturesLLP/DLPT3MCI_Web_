
import { User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useState, useRef } from "react";
import { useToast } from "@/hooks/use-toast";

export const ReportFoundSection = () => {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [matchResult, setMatchResult] = useState<{
    match_found: boolean;
    match_method?: string;
    child_name?: string;
    last_seen_location?: string;
    confidence?: number;
    notification_sent?: boolean;
    mole_match_confirmation?: boolean;
  } | null>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) {
      setSelectedImage(null);
      return;
    }
    
    const file = e.target.files[0];
    const imageUrl = URL.createObjectURL(file);
    setSelectedImage(imageUrl);
  };

  const validateForm = (formData: FormData): boolean => {
    const newErrors: Record<string, string> = {};
    
    // Validate reporter name
    const reporterName = formData.get('reporterName') as string;
    if (!reporterName || reporterName.trim() === '') {
      newErrors.reporterName = "Your name is required";
    }
    
    // Validate reporter phone
    const reporterPhone = formData.get('reporterPhone') as string;
    if (!reporterPhone || !/^\d{10}$/.test(reporterPhone)) {
      newErrors.reporterPhone = "Please enter a valid 10-digit phone number";
    }
    
    // Validate location
    const location = formData.get('location') as string;
    if (!location || location.trim() === '') {
      newErrors.location = "Location where child was found is required";
    }
    
    // Check if photo is selected
    const fileInput = document.querySelector('input[name="foundPhoto"]') as HTMLInputElement;
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      newErrors.foundPhoto = "Please select a photo";
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    // Create FormData from the form
    const formData = new FormData(e.currentTarget);
    
    // Validate the form
    if (!validateForm(formData)) {
      toast({
        title: "Validation Error",
        description: "Please correct the errors in the form",
        variant: "destructive",
      });
      return;
    }
    
    setIsSubmitting(true);
    setMatchResult(null);

    try {
      // Ensure file is included
      const fileInput = e.currentTarget.querySelector('input[type="file"]') as HTMLInputElement;
      if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        throw new Error("Please select a photo");
      }
      
      // Make sure foundPhoto is explicitly set in FormData
      formData.delete('foundPhoto'); // Remove if already exists
      formData.append('foundPhoto', fileInput.files[0]);
      
      console.log("Submitting form with file:", fileInput.files[0].name);
      
      const response = await fetch('http://localhost:5000/api/report-found', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Server error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      
      // Set the raw result for display purposes
      setMatchResult(data);

      // Determine if there's an actual match based on confidence threshold
      let isActualMatch = data.match_found;
      
      // For facial recognition, require at least 80% confidence
      if (data.match_method === 'facial_recognition' && data.confidence !== undefined) {
        isActualMatch = data.confidence >= 0.75; // 80% threshold
      }

      if (isActualMatch) {
        let matchDescription = "facial recognition";
        if (data.match_method === 'mole_description') {
          matchDescription = "mole description";
        }
        
        const locationDisplay = data.last_seen_location && data.last_seen_location !== "Unknown" 
          ? data.last_seen_location 
          : "Unknown location";
        
        toast({
          title: "Match Found!",
          description: `This child matches with ${data.child_name} (via ${matchDescription}) who was last seen at ${locationDisplay}`,
        });
      } else {
        toast({
          title: "No Match Found",
          description: data.match_method === 'facial_recognition' && data.confidence < 0.8
            ? "The facial recognition confidence is below 80%"
            : "The child could not be matched with any missing children reports.",
        });
        
        if (formRef.current) {
          formRef.current.reset();
          setSelectedImage(null);
          setErrors({});
        }
      }
    } catch (error) {
      console.error("Error submitting form:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to submit report",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Determine if match should be shown as found based on confidence threshold
  const shouldShowAsMatchFound = matchResult?.match_found && (
    matchResult.match_method === 'mole_description' || 
    (matchResult.match_method === 'facial_recognition' && 
     matchResult.confidence !== undefined && 
     matchResult.confidence >= 0.75)
  );

  return (
    <section id="report-found" className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center space-x-3 mb-6">
        <User className="w-8 h-8 text-police-blue" />
        <h2 className="text-2xl font-bold text-police-dark">Report Found Child</h2>
      </div>
      
      {matchResult && shouldShowAsMatchFound && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="font-semibold text-green-800">Match Found!</h3>
          <p className="text-green-700">
            This child matches with {matchResult.child_name} who was last seen at {matchResult.last_seen_location || 'Unknown location'}
          </p>
          
          {matchResult.match_method === 'facial_recognition' && matchResult.confidence !== undefined && (
            <p className="text-sm text-green-600 mt-1">
              Match confidence: {(matchResult.confidence * 100).toFixed(1)}%
              {matchResult.mole_match_confirmation && (
                <span className="ml-2 font-semibold">
                  (Confirmed by mole description match)
                </span>
              )}
            </p>
          )}
          
          {matchResult.match_method === 'mole_description' && (
            <p className="text-sm text-green-600 mt-1">
              Matched based on mole description
            </p>
          )}
          
          {matchResult.notification_sent !== undefined && (
            <p className={matchResult.notification_sent ? "text-sm mt-1 text-green-600" : "text-sm mt-1 text-amber-600"}>
              {matchResult.notification_sent 
                ? "SMS notification sent to parent/guardian."
                : "SMS notification could not be sent (parent phone may not be available)."}
            </p>
          )}
        </div>
      )}
      
      {/* Show no match found message when match exists but confidence is low */}
      {matchResult && matchResult.match_found && !shouldShowAsMatchFound && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <h3 className="font-semibold text-amber-800">No Confident Match Found</h3>
          <p className="text-amber-700">
            The facial recognition confidence is only {(matchResult.confidence || 0) * 100}%, which is below our 75% threshold.
          </p>
        </div>
      )}
      
      <form ref={formRef} onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="child-name">Child's Name (Optional)</Label>
            <Input 
              id="child-name" 
              name="childName"
              placeholder="Enter child's name if known" 
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="reporter-name">Your Name*</Label>
            <Input 
              id="reporter-name" 
              name="reporterName"
              placeholder="Enter your full name"
              className={errors.reporterName ? "border-red-500" : ""}
            />
            {errors.reporterName && (
              <p className="text-red-500 text-sm mt-1">{errors.reporterName}</p>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="reporter-phone">Your Phone Number*</Label>
          <Input 
            id="reporter-phone" 
            name="reporterPhone"
            type="tel"
            placeholder="Enter your phone number"
            pattern="[0-9]{10}"
            title="Please enter a valid 10-digit phone number"
            className={errors.reporterPhone ? "border-red-500" : ""}
          />
          {errors.reporterPhone && (
            <p className="text-red-500 text-sm mt-1">{errors.reporterPhone}</p>
          )}
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="location-found">Location Found*</Label>
          <Input 
            id="location-found" 
            name="location"
            placeholder="Enter location where child was found"
            className={errors.location ? "border-red-500" : ""}
          />
          {errors.location && (
            <p className="text-red-500 text-sm mt-1">{errors.location}</p>
          )}
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="additional-details">Additional Details (including mole descriptions)</Label>
          <Textarea 
            id="additional-details" 
            name="details"
            placeholder="Enter any additional details about the child, including descriptions of any visible moles (location, size, color) to help with identification"
            className="h-24"
          />
          <p className="text-sm text-muted-foreground">
            Important: If you can see any moles on the child, please describe them in detail (location, size, color).
            For example: "Small dark mole on left cheek" or "2cm brown mole on right arm".
          </p>
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="found-photo">Child's Photo (PNG, JPEG, or JPG)*</Label>
          <Input 
            id="found-photo" 
            name="foundPhoto"
            type="file" 
            accept="image/png,image/jpeg,image/jpg"
            className={errors.foundPhoto ? "border-red-500" : ""}
            onChange={handleImageChange}
          />
          {errors.foundPhoto && (
            <p className="text-red-500 text-sm mt-1">{errors.foundPhoto}</p>
          )}
        </div>

        {/* Image Preview Section */}
        {selectedImage && (
          <div className="space-y-2">
            <Label>Image Preview</Label>
            <div className="flex justify-center">
              <div className="relative w-full max-w-sm">
                <img 
                  src={selectedImage} 
                  alt="Preview" 
                  className="w-full h-60 object-contain rounded-md border border-gray-200"
                />
              </div>
            </div>
          </div>
        )}
        
        <Button 
          type="submit" 
          className="w-full bg-police-blue hover:bg-police-accent"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Submitting..." : "Submit Found Child Report"}
        </Button>
      </form>
    </section>
  );
};

