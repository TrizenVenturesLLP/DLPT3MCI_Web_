import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useState } from "react";
import { useToast } from "@/components/ui/use-toast";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export const ReportMissingSection = () => {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedImages, setSelectedImages] = useState<string[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) {
      setSelectedImages([]);
      return;
    }
    
    const imageUrls: string[] = [];
    const fileArray = Array.from(e.target.files);
    
    fileArray.forEach(file => {
      const imageUrl = URL.createObjectURL(file);
      imageUrls.push(imageUrl);
    });
    
    setSelectedImages(imageUrls);
  };

  const validateForm = (formData: FormData): boolean => {
    const newErrors: Record<string, string> = {};
    
    // Validate child name
    const childName = formData.get('childName') as string;
    if (!childName || childName.trim() === '') {
      newErrors.childName = "Child's name is required";
    }
    
    // Validate age
    const age = Number(formData.get('age'));
    if (isNaN(age) || age <= 0) {
      newErrors.age = "Age must be a positive number";
    }
    
    // Validate height
    const height = Number(formData.get('height'));
    if (isNaN(height) || height <= 0) {
      newErrors.height = "Height must be a positive number";
    }
    
    // Validate skin color
    const skinColor = formData.get('skinColor') as string;
    if (!skinColor) {
      newErrors.skinColor = "Please select skin color";
    }
    
    // Validate last seen location
    const location = formData.get('location') as string;
    if (!location || location.trim() === '') {
      newErrors.location = "Last seen location is required";
    }
    
    // Validate phone numbers
    const parentPhone = formData.get('parentPhone') as string;
    if (!parentPhone || !/^\d{10}$/.test(parentPhone)) {
      newErrors.parentPhone = "Please enter a valid 10-digit phone number";
    }
    
    const policeContact = formData.get('policeContact') as string;
    if (!policeContact || !/^\d{10}$/.test(policeContact)) {
      newErrors.policeContact = "Please enter a valid 10-digit phone number";
    }
    
    // Check if photos are selected
    const fileInput = document.querySelector('input[name="photos"]') as HTMLInputElement;
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      newErrors.photos = "Please select at least one photo";
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    // Store the form reference before any async operations
    const formElement = e.currentTarget;
    const formData = new FormData(formElement);
    
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
  
    try {
      // Ensure file input exists before accessing it
      const fileInput = formElement.querySelector('input[type="file"]') as HTMLInputElement;
      
      if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        throw new Error("Please select at least one photo");
      }
  
      // Ensure the 'photos' field is properly set
      formData.delete('photos');
      for (let i = 0; i < fileInput.files.length; i++) {
        formData.append('photos', fileInput.files[i]);
      }
  
      // Ensure the 'childName' field exists
      if (!formData.get('childName')) {
        const childNameInput = document.getElementById('childName') as HTMLInputElement;
        if (childNameInput) {
          formData.set('childName', childNameInput.value);
        }
      }
  
      const response = await fetch('http://localhost:5000/api/report-missing', {
        method: 'POST',
        body: formData
      });
  
      const data = await response.json();
  
      if (response.ok) {
        toast({
          title: "Report Submitted",
          description: "Missing child report has been submitted successfully.",
        });
  
        // Ensure the form is still in the DOM before resetting
        if (formElement) {
          formElement.reset();
          // Clear image previews
          setSelectedImages([]);
          // Clear errors
          setErrors({});
        }
      } else {
        throw new Error(data.error || 'Failed to submit report');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to submit report",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <section id="report-missing" className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center space-x-3 mb-6">
        <AlertCircle className="w-8 h-8 text-red-500" />
        <h2 className="text-2xl font-bold text-police-dark">Report Missing Child</h2>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="childName">Child's Name</Label>
            <Input 
              id="childName" 
              name="childName" 
              placeholder="Enter child's name" 
              className={errors.childName ? "border-red-500" : ""}
            />
            {errors.childName && (
              <p className="text-red-500 text-sm mt-1">{errors.childName}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="age">Age</Label>
            <Input 
              id="age" 
              name="age" 
              type="number" 
              min="1" 
              placeholder="Enter age" 
              className={errors.age ? "border-red-500" : ""}
            />
            {errors.age && (
              <p className="text-red-500 text-sm mt-1">{errors.age}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="height">Height (cm)</Label>
            <Input 
              id="height" 
              name="height" 
              type="number" 
              min="1" 
              placeholder="Enter height" 
              className={errors.height ? "border-red-500" : ""}
            />
            {errors.height && (
              <p className="text-red-500 text-sm mt-1">{errors.height}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="skinColor">Skin Color</Label>
            <Select name="skinColor">
              <SelectTrigger className={errors.skinColor ? "border-red-500" : ""}>
                <SelectValue placeholder="Select skin color" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="fair">Fair</SelectItem>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="olive">Olive</SelectItem>
                <SelectItem value="brown">Brown</SelectItem>
                <SelectItem value="dark">Dark</SelectItem>
              </SelectContent>
            </Select>
            {errors.skinColor && (
              <p className="text-red-500 text-sm mt-1">{errors.skinColor}</p>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="location">Last Seen Location</Label>
          <Input 
            id="location" 
            name="location" 
            placeholder="Enter location where child was last seen"
            className={errors.location ? "border-red-500" : ""}
          />
          {errors.location && (
            <p className="text-red-500 text-sm mt-1">{errors.location}</p>
          )}
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="distinguishingFeatures">Distinguishing Features</Label>
          <Textarea 
            id="distinguishingFeatures" 
            name="distinguishingFeatures"
            placeholder="Enter any birthmarks, moles, scars, or other distinguishing features. For moles, please specify location, size, and color (e.g., 'Small dark mole on left cheek', '2cm brown mole on right arm')"
            className="h-24"
          />
          <p className="text-sm text-muted-foreground">
            Important: Provide detailed information about any moles, including their location on the body, 
            approximate size, and color. This helps with identification.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="parentPhone">Parent/Guardian Phone</Label>
            <Input 
              id="parentPhone" 
              name="parentPhone"
              type="tel" 
              placeholder="Enter phone number"
              pattern="[0-9]{10}"
              title="Please enter a valid 10-digit phone number"
              className={errors.parentPhone ? "border-red-500" : ""}
            />
            {errors.parentPhone && (
              <p className="text-red-500 text-sm mt-1">{errors.parentPhone}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="policeContact">Police Contact Number</Label>
            <Input 
              id="policeContact" 
              name="policeContact"
              type="tel" 
              placeholder="Enter police contact number"
              pattern="[0-9]{10}"
              title="Please enter a valid 10-digit phone number"
              className={errors.policeContact ? "border-red-500" : ""}
            />
            {errors.policeContact && (
              <p className="text-red-500 text-sm mt-1">{errors.policeContact}</p>
            )}
          </div>
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="photos">Child's Photos (PNG, JPEG, or JPG)*</Label>
          <Input 
            id="photos" 
            name="photos"
            type="file" 
            accept="image/png,image/jpeg,image/jpg"
            multiple
            className={errors.photos ? "border-red-500" : ""}
            onChange={handleImageChange}
          />
          {errors.photos && (
            <p className="text-red-500 text-sm mt-1">{errors.photos}</p>
          )}
          <p className="text-sm text-muted-foreground mt-1">
            You can select multiple photos by holding Ctrl (Windows) or Command (Mac) while selecting files
          </p>
        </div>

        {/* Image Preview Section */}
        {selectedImages.length > 0 && (
          <div className="space-y-2">
            <Label>Selected Images Preview</Label>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              {selectedImages.map((imageUrl, index) => (
                <div key={index} className="relative group">
                  <img 
                    src={imageUrl} 
                    alt={`Preview ${index + 1}`} 
                    className="w-full h-32 object-cover rounded-md border border-gray-200"
                  />
                </div>
              ))}
            </div>
          </div>
        )}
        
        <Button 
          type="submit" 
          className="w-full bg-police-blue hover:bg-police-accent"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Submitting..." : "Submit Report"}
        </Button>
      </form>
    </section>
  );
};
